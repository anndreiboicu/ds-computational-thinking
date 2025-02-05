import nltk
import pandas as pd
import sys
from nltk.sentiment import SentimentIntensityAnalyzer

def main(news_file):
    """Perform sentiment analysis on the given CSV file."""
    try:
        # Read the specified CSV file
        news_df = pd.read_csv(news_file)

        # Download VADER lexicon if not already installed
        nltk.download("vader_lexicon")

        # Initialize Sentiment Analyzer
        sia = SentimentIntensityAnalyzer()

        # Function to get sentiment scores
        def analyze_sentiment(text):
            sentiment = sia.polarity_scores(str(text))  # Ensure text is a string
            if sentiment["compound"] >= 0.05:
                return "Bullish"
            elif sentiment["compound"] <= -0.05:
                return "Bearish"
            else:
                return "Neutral"

        # Apply sentiment analysis to the news DataFrame
        news_df["Sentiment"] = (news_df["Title"] + " " + news_df["Short Description"]).apply(analyze_sentiment)
        news_df = news_df[["Sentiment"] + [col for col in news_df.columns if col != "Sentiment"]]

        # Save the updated data back to the same CSV file
        news_df.to_csv(news_file, index=False)
        print(f"Sentiment analysis completed. Updated file saved as '{news_file}'.")

    except FileNotFoundError:
        print(f"Error: The file '{news_file}' was not found.")
    except Exception as e:
        print(f"Unexpected error: {e}")

# If run as a script, accept the file name as a command-line argument
if __name__ == "__main__":
    if len(sys.argv) > 1:
        news_file = sys.argv[1]  # Get file name from command line
        main(news_file)
    else:
        print("Error: No news file specified. Usage: python sentimentAnalysis.py <news_file>")
