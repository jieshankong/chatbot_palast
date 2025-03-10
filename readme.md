# Chatbot Prototype for Friedrichstadt-Palast
This is a chatbot prototype built with **Rasa 3.1**. It is designed to answer **standard guest inquiries** about the Friedrichstadt-Palast.

## Folder Structure
```bash
📂 rasa  
│── 📂 data               # Training data (NLU, stories, rules)  
│   ├── nlu.yml           # User messages and intents  
│   ├── stories.yml       # Example conversations  
│   ├── rules.yml         # Simple response rules  
│  
│── 📂 models             # Trained Rasa models  
│  
│── 📂 actions            # Custom action server (if needed)  
│   ├── actions.py        # Custom Python actions 
│   ├── event.csv         # Temp solution for getting event information without connection to the data warehouse  
│   ├── fetch_event.sql   # Query to get event information from the internal data warehouse    
│  
│── 📂 config             # Configuration files  
│   ├── config.yml        # Rasa pipeline and policies  
│  
│── 📂 domain             # Bot responses and entities  
│   ├── domain.yml        # Bot responses and settings  
│  
│── .gitignore            # Files to ignore in version control  
│── requirements.txt      # Python dependencies  
│── README.md             # Project documentation  
│── credentials.yml       # Credentials for messaging platforms  
│── endpoints.yml         # Configuration for action server  
```

## Features
- Responds to frequently asked questions (FAQs)
- Understands and replies in German
- Uses machine learning (NLU) to recognize guest questions
- Can be improved with more training data

## Installation
1. Clone the repository 
```bash
git clone <your-repo-url>
cd <your-repo-folder>
```
2. Create a virtual environment (optional but recommended)
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
```
3. Install dependencies
```bash
pip install -r requirements.txt
```
## Running the Chatbot
1. Train the model:
```bash
rasa train
```
2. Start the chatbot (in another terminal):
```bash
rasa run actions
```
3. Start the chat interface:
```bash
rasa shell
```
## Customization
- Modify `data/nlu.yml` to add new user questions
- Edit `domain.yml` to update bot responses
- Adjust rules and stories in `data/rules.yml` and `data/stories.yml`
## Deployment
For production, consider using Rasa X or a Rasa server with a custom UI.

## License
This project is private and not open-source. Redistribution or public sharing is not allowed without permission.