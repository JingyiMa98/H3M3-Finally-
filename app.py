from flask import Flask, render_template, request, jsonify,session
import openai
import requests

app = Flask(__name__)
app.secret_key = 'asdoasojdaosjd21sdasd0a0sd'  # Set a secret key for session management

# OpenAI API Key
openai.api_key = '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'

# Yelp API Key
YELP_API_KEY = '2OFdPJVezMcmDick8CtTtuGrknkwDW9c7mBQju6ELglHV1bnHmFaSfMlSC7gx4VaPRadikR2orkG7CIlkcNvF9s1uDyRnJuQdP2i5nSxr9pws_RQYNajIOQflONTZ3Yx'
YELP_API_URL = "https://api.yelp.com/v3/businesses/search"


def get_nearest_restaurants(location, food_type, limit=3):
    headers = {"Authorization": f"Bearer {YELP_API_KEY}"}
    params = {"location": location, "term": food_type, "limit": limit}
    response = requests.get(YELP_API_URL, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        if data["businesses"]:
            restaurants = []
            for business in data["businesses"]:
                restaurants.append({
                    "name": business["name"],
                    "address": ", ".join(business["location"]["display_address"]),
                    "rating": business.get("rating", "N/A"),
                    "image_url": business.get("image_url", ""),
                    "url": business.get("url", ""),
                })
            return restaurants
    return {"error": "No restaurants found."}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    if request.method == 'POST':
        user_message = request.json.get('message')

        # Extract the food type and location using OpenAI
        completion = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant extracting food type and location from user messages."},
                {"role": "user", "content": f"Extract the food type and location from the message: '{user_message}'."}
            ],
            max_tokens=50
        )

        extracted = completion.choices[0].message.content
        print("OpenAI response:", extracted)

        lines = extracted.split('\n')
        food_type = None
        location = None

        for line in lines:
            if line.lower().startswith("food type:"):
                food_type = line.split(":", 1)[1].strip()
            elif line.lower().startswith("location:"):
                location = line.split(":", 1)[1].strip()

        # If no location is mentioned, use the previously stored location from the session
        if not location or location.lower() == "not specified":
            location = session.get('location', None)
        else:
            # Store the location in session for future requests
            session['location'] = location


        # Validate extraction
        if not food_type:
            return jsonify({"reply": "Sorry, I couldn't understand the food type. Please try again."})

        if not location:
            return jsonify({"reply": "Please include a location in your request."})


        # Get multiple restaurant details from Yelp
        restaurants = get_nearest_restaurants(location, food_type)

        if "error" in restaurants:
            return jsonify({"reply": "Sorry, no restaurants were found."})

        # Format the response with multiple options
        reply = "Here are some options for you:\n"
        restaurant_info = []
        for restaurant in restaurants:
            restaurant_info.append({
                "name": restaurant["name"],
                "address": restaurant["address"],
                "rating": restaurant["rating"],
                "image_url": restaurant["image_url"],
                "url": restaurant["url"]
            })
        
        return jsonify({"reply": reply, "restaurants": restaurant_info})

    return render_template('chatbot.html')


if __name__ == '__main__':
    app.run(debug=True,port=80)
