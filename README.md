# Web-Scraping-and-ChatGPT

This project is a web scraping application that extracts cryptocurrency news articles from various sources, processes the content using OpenAI's GPT-3.5-turbo model, and sends notifications via email if certain conditions are met. The application is designed to run continuously, checking for new articles at regular intervals.

## Features

- **Web Scraping**: Utilizes Selenium and BeautifulSoup to navigate and extract content from cryptocurrency news websites.
- **AI Processing**: Sends extracted content to OpenAI's GPT-3.5-turbo model for processing and analysis.
- **Email Notifications**: Sends email alerts if content cannot be accessed or processed.
- **Data Storage**: Saves AI responses to a JSON file for record-keeping and further analysis.

## Prerequisites

- Python 3.x
- Google Chrome browser

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/nasuheren/Web-Scraping-and-ChatGPT.git
   cd Web-Scraping-and-ChatGPT
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your environment variables by creating a `.env` file in the root directory with the following keys:
   ```
   OPEN_API_KEY=your_openai_api_key
   GONDERICI_MAIL=your_sender_email
   GONDERICI_MAIL_PASSWORD=your_email_password
   ALICI_MAIL=your_recipient_email
   ```

## Usage

Run the main script to start the application: python main.py