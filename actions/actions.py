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
                'adac': r'\b(adac)\b',
                'student': r'\b(student|azubi|schüler|kind|auszub|jugendlich)\b',
                'disable': r'\b(schwerbehinderung|behindert|gdb)\b',
                'berlin_welcome_card': r'\b(berlin[-\s]?welcom?e[-\s]?card)\b',
                'young_ticket': r'\b(young[-\s]?ticket)\b',
                'senior': r'\b(senior|rentner)\b',
                'unemployed': r'\b(arbeitslos|alg)\b',
                'pfa': r'\b(pfa|palast[-\s]?für[-\s]?alle)\b'
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

        # Normalize date by replacing non-standard separators with '.'
        user_date_str = re.sub(r"[-/]", ".", user_date_str)

        # Check if year is missing and append current year if necessary
        if len(user_date_str.split('.')) == 2:
            user_date_str += f".{datetime.now().year}"

        # Replace German month names with numbers
        month_names = {
            "Jan": "01", "Januar": "01", "Feb": "02", "Februar": "02",
            "Mär": "03", "März": "03", "Apr": "04", "April": "04",
            "Mai": "05", "Jun": "06", "Juni": "06", "Jul": "07",
            "Juli": "07", "Aug": "08", "August": "08", "Sep": "09",
            "Sept": "09", "September": "09", "Okt": "10", "Oktober": "10",
            "Nov": "11", "November": "11", "Dez": "12", "Dezember": "12"
        }
        for name, num in month_names.items():
            user_date_str = user_date_str.replace(name, num)

        # Path to the CSV file
        base_path = os.getenv('BASE_PATH', r'C:\Users\kong\PycharmProjects\test\rasa\actions')
        csv_file_path = os.path.join(base_path, 'event.csv')

        try:
            df = pd.read_csv(csv_file_path, sep=";")
            df['date'] = pd.to_datetime(df['date'], format="%d.%m.%Y").dt.date

            # Convert user_date_str to date object
            event_date = datetime.strptime(user_date_str, "%d.%m.%Y").date()

            # Filter events by the specified date
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
