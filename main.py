import json
from fastapi import FastAPI, HTTPException, Query
from mangum import Mangum
import os
import anthropic
import http.client
import urllib.parse
import json
import requests


app = FastAPI()
handler = Mangum(app)

# Set up the Anthropic API client
client = anthropic.Client(api_key=ANTHROPIC_API_KEY)

@app.get("/")
async def root():
    return {"message": "Welcome to many AI API"}

@app.get("/generate")
async def generate(url: str):
    if not url:
        raise HTTPException(status_code=400, detail="Please enter a LinkedIn URL")

    try:
        user_details = get_linkedin_user_details(url)
        if not user_details:
            raise HTTPException(status_code=404, detail="User details not found")

        posts_data = get_linkedin_posts(url)
        if not posts_data:
            raise HTTPException(status_code=404, detail="Posts data not found")

        user_info = all_info(user_details, posts_data)
        if not user_info:
            raise HTTPException(status_code=404, detail="Failed to compile user information")

        analysis_results = linkedin_analysis(user_info)
        return analysis_results

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_linkedin_user_details(url: str):
    return make_api_call(url, "/get-linkedin-profile")

def get_linkedin_posts(url: str):
    return make_api_call(url, "/get-profile-posts")

def make_api_call(url: str, endpoint: str):
    encoded_url = urllib.parse.quote(url, safe='')
    conn = http.client.HTTPSConnection("fresh-linkedin-profile-data.p.rapidapi.com")
    headers = {
        'X-RapidAPI-Key': RAPID_API,
        'X-RapidAPI-Host': "fresh-linkedin-profile-data.p.rapidapi.com"
    }
    conn.request("GET", f"{endpoint}?linkedin_url={encoded_url}", headers=headers)
    res = conn.getresponse()
    if res.status != 200:
        return None
    data = res.read().decode("utf-8")
    return json.loads(data)

def all_info(user_details, posts_data):
    all_info = f"\nUserDetails: {user_details} \n"
    posts = posts_data.get('data', [])

    for i, post in enumerate(posts):
        content = f"\nPost {i}: Content: {post.get('text', 'No content available')}"
        title = post.get('article_title', '')
        subtitle = post.get('article_subtitle', '')
        if title and subtitle:
            content += f", Title: {title}, Subtitle: {subtitle}"
        all_info += content

    return all_info
        
#Anthropic Call
def linkedin_analysis(info):
    try:
        prompt = f"""
            You are an expert LinkedIn profile analyzer and conversation starter. Your goal is to thoroughly analyze a user's LinkedIn profile to uncover not just their professional achievements, but also their personal interests, passions, and side projects that may not be immediately obvious. 
            
            <profile_info>
            {info}
            </profile_info>
            
            For each profile, please follow this process:

            1. Carefully review the user's summary, current role, and profile URL. Note any key details that stand out.
            2. Dig deeper into the user's posts, interactions, and activity to identify specific professional interests, skills, expertise, and goals. Look for recurring themes or notable accomplishments. 
            3. Pay special attention to more subtle details that hint at the user's personal passions, hobbies, volunteer work, or side projects. These are often great conversation starters.
            4. Craft thoughtful, open-ended questions about these personal interests that will make the user feel understood and enthusiastic to engage in further discussion. Avoid generic questions in favor of specific ones that demonstrate you've really analyzed their profile.
            5. Organize your analysis into clear sections:
            - Professional Interests  
            - Skills & Expertise
            - Professional Goals
            - Personal Interests & Conversation Starters

            Use bullet points to keep the information scannable and easy to digest. 

            The ultimate aim is to provide a comprehensive, insightful analysis of the individual that goes beyond surface-level details, and to spark authentic conversations by identifying unique angles relevant to that person's passions and experiences. Let your natural curiosity and care for others shine through.
            Do not hallucinate or fabricate any information. If some piece of information requested above is not found in the data, simply skip that part. Do not write things like "not found in post". 
            Provide your full response inside <result> tags.
            
            """
        
        response = client.messages.create(
            
            model="claude-3-opus-20240229",
            temperature = 0,
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        if not response or 'error' in response:
            raise ValueError("Failed to retrieve analysis from AI model")
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
   
