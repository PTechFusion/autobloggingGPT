
# Video to WordPress Posts

Convert YouTube video captions into blog articles using ChatGPT and automatically post them to a WordPress website.

## Features:

- Upload a CSV file containing YouTube video links.
- Retrieve captions from the YouTube videos.
- Convert captions into HTML blog posts using ChatGPT.
- Post the generated blog articles to a WordPress site.

## Installation:

1. Clone the repository:
   ```
   git clone <repository-url>
   ```

2. Install the required libraries:
   ```
   pip install streamlit youtube_transcript_api openai pandas bs4 requests
   ```

## Usage:

1. Run the Streamlit application:
   ```
   streamlit run <app_filename>.py
   ```

2. Navigate to the provided link and follow the on-screen instructions to upload a CSV file and configure the settings.

## Security:

Make sure not to expose your API keys or any sensitive information. It's recommended to use environment variables or other secure means to keep your secrets.

## Dependencies:

- streamlit
- youtube_transcript_api
- openai
- pandas
- bs4
- requests

## Contributing:

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License:

[MIT](https://choosealicense.com/licenses/mit/)

