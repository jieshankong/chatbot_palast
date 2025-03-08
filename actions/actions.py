# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import UserUtteranceReverted
from rasa_sdk.events import FollowupAction
from rasa_sdk.events import SlotSet
import os
import pandas as pd
from datetime import datetime
import re

class ActionDefaultFallback(Action):

    def name(self) -> Text:
        return "action_default_fallback"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(template="utter_default")

        return [UserUtteranceReverted()]



class ActionHandleTicketInquiry(Action):
    def name(self) -> Text:
        return "action_handle_ticket_booked_palast"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        intent_name = tracker.latest_message['intent'].get('name')

        if intent_name == "ask_print_ticket":
            dispatcher.utter_message(response="utter_print_ticket")
        elif intent_name == "ask_not_get_ticket":
            dispatcher.utter_message(response="utter_not_get_ticket")
        elif intent_name == "ask_ticket_rebooking":
            dispatcher.utter_message(response="utter_ticket_rebooking")
        else:
            dispatcher.utter_message(response="utter_ticket_booked_palast")

        return []


class ActionFetchCurrentShowName(Action):

    def name(self) -> Text:
        return "action_fetch_current_show_name"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Check if show_name is already set
        show_name = tracker.get_slot("show_name")
        if not show_name:
            user_input = tracker.latest_message.get('text').lower()
            synonyms = {"falling": "FALLING | IN LOVE", "fil": "FALLING | IN LOVE"}
            for key, value in synonyms.items():
                if key in user_input:
                    show_name = value
                    break
            else:
                show_name = "FALLING | IN LOVE"  # Default to current show if no synonym is found

        # Set the show_name slot
        SlotSet("show_name", show_name)

        # Determine next step based on intent
        intent = tracker.get_intent_of_latest_message()
        if intent == "show_spielzeit":
            return [SlotSet("show_name", show_name), FollowupAction("utter_show_spielzeit")]
        elif intent == "show_dauer":
            return [SlotSet("show_name", show_name), FollowupAction("utter_show_dauer")]
        else:
            return [SlotSet("show_name", show_name)]


class ActionCheckDiscount(Action):
    def name(self):
        return "action_provide_dynamic_discount"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Get the original message
        message_text = tracker.latest_message.get('text', '').lower()

        # First try to get the entity directly
        discount_type = next(tracker.get_latest_entity_values("discount_type"), None)
        if discount_type:
            discount_type = discount_type.strip().lower()

        # If no entity found or empty after cleaning, try regex patterns
        if not discount_type:
            patterns = {
                'adac': r'\b(adac|adac[-\s]?mitglied(schaft)?)\b',
                'student': r'\b(student(in)?|student(en)?|azubi|azubis|schüler(in)?|studierende[r]?|kind(er)?)\b',
                'disable': r'\b(schwerbehind\w*|schwerbesch\w*|gdb)\b',
                'berlin_welcome_card': r'\b(berlin.*welcome.*card|berlin.*welcome|welcome.*card.*berlin)\b',
                'young_ticket': r'\b(jugendlich|unter 25|junge\w*)\b',
                'senior': r'\b(senior|rentner|älter|ab 65)\b',
                'unemployed': r'\b(sozialhilf\w*|arbeitslos\w*|erwerbslos\w*)\b',
                'pfa': r'\b(pfa|palast für alle)\b'
            }

            for disc_type, pattern in patterns.items():
                if re.search(pattern, message_text, re.IGNORECASE):
                    discount_type = disc_type
                    break

        # Return with appropriate FollowupAction
        if discount_type:
            return [
                SlotSet("discount_type", discount_type),
                FollowupAction(f"utter_discount_{discount_type}")
            ]
        else:
            return [
                SlotSet("discount_type", None),
                FollowupAction("utter_ask_specific_discount")
            ]


class ActionCheckEvents(Action):
    def name(self) -> Text:
        return "action_check_events"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        user_date_str = tracker.get_slot("event_date")  # User-provided date
        if not user_date_str:
            dispatcher.utter_message(text="Bitte geben Sie ein Datum ein.")
            return []

        try:
            # Remove extra spaces and convert to lowercase
            user_date_str = " ".join(user_date_str.lower().split())

            # Extract date pattern from the sentence - improved pattern
            date_pattern = r'(\d{1,2}\.?\s*(?:jan(?:uar)?|feb(?:ruar)?|mär(?:z)?|mrz\.?|apr(?:il)?|mai|jun(?:i)?|jul(?:i)?|aug(?:ust)?|sep(?:t)?(?:ember)?|okt(?:ober)?|nov(?:ember)?|dez(?:ember)?)|(?:\d{1,2})[-\s.\/]+(?:\d{1,2}))(?:[-\s.\/]+\d{4})?'
            match = re.search(date_pattern, user_date_str, re.IGNORECASE)

            if match:
                user_date_str = match.group(0)  # Changed from group(1) to group(0)
            else:
                raise ValueError("Kein Datum gefunden")

            # Normalize separators: replace multiple spaces, slashes, or dashes with a single dot
            user_date_str = re.sub(r'[\s/\-]+', '.', user_date_str)

            # Remove any spaces around dots
            user_date_str = re.sub(r'\s*\.\s*', '.', user_date_str)

            # German month names mapping (including abbreviations)
            month_names = {
                "jan": "01", "januar": "01",
                "feb": "02", "februar": "02",
                "mär": "03", "märz": "03", "mrz": "03",
                "apr": "04", "april": "04",
                "mai": "05",
                "jun": "06", "juni": "06",
                "jul": "07", "juli": "07",
                "aug": "08", "august": "08",
                "sep": "09", "sept": "09", "september": "09",
                "okt": "10", "oktober": "10",
                "nov": "11", "november": "11",
                "dez": "12", "dezember": "12"
            }

            # Replace month names with numbers
            for name, num in month_names.items():
                user_date_str = re.sub(rf'\b{name}\.?\b', num, user_date_str, flags=re.IGNORECASE)

            # Remove any trailing dots
            user_date_str = user_date_str.rstrip('.')

            # Split the date parts
            date_parts = [part for part in re.split(r'[.\-/\s]+', user_date_str) if part]

            # Pad day and month with leading zeros if necessary
            if len(date_parts) >= 2:
                date_parts[0] = date_parts[0].zfill(2)
                date_parts[1] = date_parts[1].zfill(2)

            # Handle different date part counts
            if len(date_parts) == 2:
                date_parts.append(str(datetime.now().year))
            elif len(date_parts) == 3 and len(date_parts[2]) == 0:
                date_parts[2] = str(datetime.now().year)

            # Reconstruct the date string
            user_date_str = '.'.join(date_parts)

            # Rest of the code remains the same
            base_path = os.getenv('BASE_PATH', r'C:\Users\kong\PycharmProjects\test\rasa\actions')
            csv_file_path = os.path.join(base_path, 'event.csv')

            df = pd.read_csv(csv_file_path)
            df['date'] = pd.to_datetime(df['date'], format="%d.%m.%Y").dt.date

            event_date = datetime.strptime(user_date_str, "%d.%m.%Y").date()

            filtered_events = df[df['date'] == event_date]

            if not filtered_events.empty:
                event_details = ', '.join(filtered_events['event_name'].tolist())
                message = f"Am {event_date.strftime('%d.%m.%Y')}, finden folgende Veranstaltungen statt: {event_details}."
            else:
                message = f"Am {event_date.strftime('%d.%m.%Y')} finden keine Veranstaltungen statt."

        except ValueError as e:
            message = f"Ungültiges Datumsformat: {str(e)}"
        except FileNotFoundError:
            message = f"Die CSV-Datei wurde nicht gefunden unter: {csv_file_path}."
        except Exception as e:
            message = f"Fehler beim Abrufen von Veranstaltungen: {str(e)}"

        dispatcher.utter_message(text=message)
        return []