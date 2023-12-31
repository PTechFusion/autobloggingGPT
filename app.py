import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
import urllib.parse
import openai
from openai.error import ServiceUnavailableError, Timeout
import csv
import requests
from bs4 import BeautifulSoup
import yaml
from yaml.loader import SafeLoader
from streamlit_authenticator import Authenticate
from stqdm import stqdm
with open('auth.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)
# from dotenv import dotenv_values

import time
# config1 = dotenv_values(".env")

authenticator = Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)



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
def check_password(submitted_password):
    if submitted_password == "streamlit":
        return True
    return False
#admintest12345
def page_one():
    name, authentication_status, username = authenticator.login('Login', 'main')
    st.subheader("ChatGPT & Links")
    # st.session_state["selected_website"]=config1.get("WP_URL")
    # st.session_state['openai_api_key']=config1.get("OPEN_AI_API")
    # st.session_state['wp_login']=config1.get("WP_USER")
    # st.session_state['wp_password']=config1.get("WP_APP_PWD")
    # st.session_state['add_video'] = True
    # ChatGPT Prompt
    if st.session_state["authentication_status"]:
        authenticator.logout('Logout', 'main')
        st.write(f'Welcome *{st.session_state["name"]}*')
        
        chatgpt_prompt = st.text_input(label="ChatGPT Prompt:", placeholder='I want you to generate a blog based on the content in HTML format')
        urls = None
        urls_count = 0
        # YouTube Links CSV
        uploaded_file = st.file_uploader(label="Upload YouTube links CSV:", type=["csv"])

        # Replace with the actual path to your CSV file
        csv_file_path = uploaded_file
        if uploaded_file is not None:
            urls = [x for x in list(csv.reader((line.decode('utf-8') for line in csv_file_path), delimiter=',')) if x]
            urls_count = len(urls)
            st.session_state['csv_reader'] = urls
                
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

            if urls_count<=100:
                step_size = int(100/urls_count)
            else:
                step_size = (100/urls_count)
            
            i = 0
            for row in stqdm(st.session_state['csv_reader']):
                try:
                # Access the value in the 0th column (first column)
                
                    value_in_first_column = row[0]
                    if not value_in_first_column:
                        continue
                    print(i)
                    # ic('----',value_in_first_column)
                    url = value_in_first_column
                    video_id = get_video_id_from_url(url)
                    try:
                        caption_data = YouTubeTranscriptApi.get_transcript(video_id=video_id, languages=('en','es','fr',))
                    except Exception as e:
                        
                        i += step_size
                        
                        
                        progress_bar.progress(int(i))
                        continue
                    
                    merged_text = ' '.join(item['text'] for item in caption_data)
                    
                    
                    prompt = chatgpt_prompt  + merged_text + "\n Please only response with HTML. Only HTML with at least one title tag and some h2 headings"
                    while True:
                        try:
                            response = openai.ChatCompletion.create(
                            model="gpt-3.5-turbo-16k",
                            messages=[
                                {'role': 'user', 'content': prompt}
                            ],
                            temperature=0.7,
                            max_tokens=4000,
                            )
                            break
                        except ServiceUnavailableError:
                            print('Open AI Server is unavailable, retrying...')
                            time.sleep(5)
                        except Timeout:
                            print('Open AI Server Timeout, retrying...')
                            time.sleep(5)
                    html_string = response.choices[0].message.content
                    with open('output.html', 'w', encoding='utf-8') as f:
                        f.write(html_string)
                    
                    soup = BeautifulSoup(html_string, 'html.parser')
                    title = "Blog Post"
                    title_tag = soup.find('title')
                    if title_tag:
                        title = title_tag.text.strip()
                        # title_tag = soup.extract('title')
                        soup.find('title').decompose()
                        h1 = soup.find('h1')
                        if h1:
                            h1.decompose()
                    else:
                        title_tag = soup.find('h1')
                        if title_tag:
                            title = title_tag.text.strip()
                            # # title_tag = soup.extract('title')
                            # soup.find('title').decompose()
                            h1 = soup.find('h1')
                            if h1:
                                h1.decompose()
                    print(title)
                    # Create a JSON payload for the new post
                    if st.session_state['add_video']:
                        content = str(soup.find('body')) + f'\n{value_in_first_column}'
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
                except Exception as e:
                    print(f'Had an error in getting the HTML\n{e}')
                    
                i += step_size
                progress_bar.progress(int(i))
                # progress_bar.text(f"{i}/{len(list(st.session_state['csv_reader']))}")
                
            # Your processing logic here for page 1
            st.write("Data from Page 1 saved!")
    elif st.session_state["authentication_status"] == False:
        st.error('Username/password is incorrect')
    elif st.session_state["authentication_status"] == None:
        st.warning('Please enter your username and password')
def page_two():
    st.subheader("Settings")
    
    name, authentication_status, username = authenticator.login('Login', 'main')
    if st.session_state["authentication_status"]:
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
    elif st.session_state["authentication_status"] == False:
        st.error('Username/password is incorrect')
    elif st.session_state["authentication_status"] == None:
        st.warning('Please enter your username and password')

def main():

    st.title("Video to Wordpress Posts")
    
    # Sidebar menu
    menu = ["ChatGPT & Links", "Settings"]
    choice = st.sidebar.radio("Auto Blogger", menu)
    
    if choice == "ChatGPT & Links":
        page_one()

    elif choice == "Settings":
        page_two()

if __name__ == "__main__":
    main()