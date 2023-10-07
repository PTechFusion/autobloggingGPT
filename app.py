import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
import urllib.parse
import openai
import csv
import requests
from bs4 import BeautifulSoup
# from dotenv import dotenv_values

# config = dotenv_values(".env")

def read_csv_to_list_of_lists(uploaded_file):
    # Check if the file is not None
    if uploaded_file is None:
        return []

    # Use the csv.reader to read the uploaded file directly
    reader = csv.reader(uploaded_file)
    data = list(reader)
    return data

def get_video_id_from_url(video_url):
    # Parse the URL
    parsed_url = urllib.parse.urlparse(video_url)
    # Extract the query parameters
    query_params = urllib.parse.parse_qs(parsed_url.query)
    
    # Get the 'v' parameter (video ID)
    video_id = query_params.get('v')
    
    # Check if 'v' parameter exists and return the first one (there should only be one)
    if video_id:
        return video_id[0]
    else:
        return None


def page_one():
    # st.subheader("Page 1: ChatGPT & Links")
    # st.session_state["selected_website"]=config.get("WP_URL")
    # st.session_state['openai_api_key']=config.get("OPEN_AI_API")
    # st.session_state['wp_login']=config.get("WP_USER")
    # st.session_state['wp_password']=config.get("WP_APP_PWD")
    # st.session_state['add_video'] = True
    # ChatGPT Prompt
    chatgpt_prompt = st.text_input(label="ChatGPT Prompt:", placeholder='I want you to generate a blog based on the content in HTML format')
    
    # YouTube Links CSV
    uploaded_file = st.file_uploader(label="Upload YouTube links CSV:", type=["csv"])

    # Replace with the actual path to your CSV file
    csv_file_path = uploaded_file
    if uploaded_file is not None:
        # Read the CSV file and store it in the state variable
            st.session_state['csv_reader'] = list(csv.reader((line.decode('utf-8') for line in csv_file_path), delimiter=','))
            
    if st.button(label="Submit"):
        # Set your API key
        openai.api_key = st.session_state['openai_api_key']
        # Define your WordPress website URL and authentication credentials
        if st.session_state['selected_website'].endswith('/'):
            wordpress_url = f'{st.session_state["selected_website"]}wp-json/wp/v2/posts'
        else:
            wordpress_url = f'{st.session_state["selected_website"]}/wp-json/wp/v2/posts'
        
        # Iterate through the rows in the CSV file
        # next(st.session_state['csv_reader'], None)
        # Iterate through the rows in the CSV file
        progress_bar = st.progress(0, text="Processing... Please wait")
        step_size = int(100/len(list(st.session_state['csv_reader'])))
        i = 0
        for row in st.session_state['csv_reader']:
            
            # Access the value in the 0th column (first column)
            value_in_first_column = row[0]
            print('----',value_in_first_column)
            url = value_in_first_column
            video_id = get_video_id_from_url(url)
            try:
                caption_data = YouTubeTranscriptApi.get_transcript(video_id=video_id,languages=('en','es','fr',))
            except:
                i += step_size
                progress_bar.progress(i)
                continue
            merged_text = ' '.join(item['text'] for item in caption_data)
            prompt = chatgpt_prompt  + merged_text+ "\nAlso, Output format has to be in plain HTML. Also output language should be in same language as the context unless specified this prompt."
            
            response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            messages=[
                {'role': 'user', 'content': prompt}
            ],
            temperature=0,
            max_tokens=4000,
            )
            html_string = response.choices[0].message.content
            with open('output.html', 'w', encoding='utf-8') as f:
                f.write(html_string)

            soup = BeautifulSoup(html_string, 'html.parser')
            # Find the <title> tag and extract its text
            title_tag = soup.find('title')
            title_tag = title_tag.extract()
            soup.find('h1').decompose()
            title = title_tag.text
            # Create a JSON payload for the new post
            if st.session_state['add_video']:
                content = str(soup.find('body')) + f'<a href="{value_in_first_column}">Video URL</a>'
            else:
                content = str(soup.find('body'))
            post_data = {
                'title': title,
                'content': content,
                'status': 'publish',  # You can set it to 'draft' if you want to save it as a draft.
            }
            username = st.session_state['wp_login']
            password = st.session_state['wp_password']
            # Make a POST request to create the new post
            response = requests.post(
                wordpress_url,
                json=post_data,
                auth=(username, password)
            )
            # Check the response
            if response.status_code == 201:
                print('Blog post created successfully!')
            else:
                print('Failed to create blog post. Status code:', response.status_code)
                print('Response content:', response.text)
            i += step_size
            progress_bar.progress(i)
            
        # Your processing logic here for page 1
        st.write("Data from Page 1 saved!")

def page_two():
    st.subheader("Page 2: Settings")
    
    opeai_api_key = st.text_input(label="OpenAI API Key:")
    # YT API
    yout_api_key = st.text_input(label="YouTube API Key:")

    # Enter website to post
    selectd_website = st.text_input(label="Enter the URL of website where articles will be uploaded : ", placeholder='https://your-wordpress-site.com')

    # Checkbox for adding video
    add_vide = st.checkbox(label="Add the video at the end of the article?")
    
    # WordPress Credentials
    wp_log = st.text_input(label="WP Login:")
    wp_pass = st.text_input(label="WP Application Password:", type="password")

    if st.button(label="Save Settings"):
        st.session_state['add_video'] = add_vide
        if opeai_api_key != '' or opeai_api_key != None:
            st.session_state['openai_api_key'] = opeai_api_key
        if yout_api_key != '' or yout_api_key != None:
            st.session_state['yt_api_key'] = yout_api_key
        if selectd_website != '' or selectd_website != None:
            st.session_state['selected_website'] = selectd_website
        if wp_log != '' or wp_log != None:
            st.session_state['wp_login'] = wp_log
        if wp_pass != '' or wp_pass != None:
            st.session_state['wp_password'] = wp_pass
        # Your processing logic here for page 2
        print(st.session_state["selected_website"])
        st.write("Settings saved!")

def main():

    st.title("Video to Wordpress Posts")

    # Sidebar menu
    menu = ["Page 1: ChatGPT & Links", "Page 2: Settings"]
    choice = st.sidebar.radio("Auto Blogger", menu)
    
    if choice == "Page 1: ChatGPT & Links":
        page_one()

    elif choice == "Page 2: Settings":
        page_two()

if __name__ == "__main__":
    main()