import os
import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput, Select
import itertools
import json

# Get the token from the environment variable
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Define the bot with the command prefix '!'
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Define a list to keep track of which questions are required
required_questions = [False] * 5

# Define a dictionary to store request details by request ID
requests = {}
request_id_counter = itertools.count(1)

# Define a flag to control request availability, defaulting to unlocked
requests_open = True

# Define the path to the requests.json file
REQUESTS_FILE_PATH = 'requests.json'

# Load requests from the JSON file
def load_requests():
    global requests, request_id_counter
    if os.path.exists(REQUESTS_FILE_PATH):
        with open(REQUESTS_FILE_PATH, 'r') as file:
            data = json.load(file)
            requests = data.get('requests', {})
            start_id = data.get('last_request_id', 1) + 1
            request_id_counter = itertools.count(start_id)
    else:
        requests = {}
        request_id_counter = itertools.count(1)

# Save requests to the JSON file
def save_requests():
    data = {
        'requests': requests,
        'last_request_id': next(request_id_counter) - 1
    }
    with open(REQUESTS_FILE_PATH, 'w') as file:
        json.dump(data, file)

# Load existing requests when the bot starts
load_requests()

# Define the modal class with specified questions
class SurveyModal(Modal):
    def __init__(self, required_status):
        super().__init__(title="Survey")
        self.required_status = required_status

        self.add_item(TextInput(label="Level Name", required=self.required_status[0]))
        self.add_item(TextInput(label="Level ID", required=self.required_status[1]))
        self.add_item(TextInput(label="Difficulty", required=self.required_status[2]))
        self.add_item(TextInput(label="Video", required=self.required_status[3]))
        self.add_item(TextInput(label="Note", required=self.required_status[4]))

    async def on_submit(self, interaction: discord.Interaction):
        level_id = self.children[1].value

        # Generate a numerical request ID
        request_id = next(request_id_counter)

        # Store the request details
        requests[request_id] = {
            'author_id': interaction.user.id,
            'author_mention': interaction.user.mention,
            'level_id': level_id,
            'responses': {
                'Level Name': self.children[0].value,
                'Level ID': level_id,
                'Difficulty': self.children[2].value,
                'Video': self.children[3].value,
                'Note': self.children[4].value,
            },
            'message_id': interaction.message.id  # Store the message ID
        }

        # Save the request details to the JSON file
        save_requests()

        # Create an embed with the responses
        embed = discord.Embed(title="Request", color=discord.Color.blue())
        embed.set_author(name=f"User ID: {interaction.user.id}", icon_url=interaction.user.avatar.url)

        embed.add_field(name="Level Name", value=self.children[0].value, inline=False)
        embed.add_field(name="Level ID", value=level_id, inline=False)
        embed.add_field(name="Difficulty", value=self.children[2].value, inline=False)
        embed.add_field(name="Video", value=self.children[3].value, inline=False)
        embed.add_field(name="Note", value=self.children[4].value, inline=False)
        embed.set_footer(text=f"Request ID: {request_id}")

        # Create a button and dropdown menu
        button_view = FeedbackView(request_id)
        message = await interaction.channel.send(embed=embed, view=button_view)
        requests[request_id]['message_id'] = message.id  # Store the message ID

        # Save the request details with the message ID
        save_requests()

        await interaction.response.send_message("Request submitted successfully!", ephemeral=True)

# Define a modal for feedback
class FeedbackModal(Modal):
    def __init__(self, option, request_id, feedback_author):
        super().__init__(title=f"Feedback - {option}")
        self.option = option
        self.request_id = request_id
        self.feedback_author = feedback_author
        self.add_item(TextInput(label="Reason", style=discord.TextStyle.paragraph, required=True))

    async def on_submit(self, interaction: discord.Interaction):
        reason = self.children[0].value

        if self.request_id in requests:
            original_author_mention = requests[self.request_id]['author_mention']
            level_id = requests[self.request_id]['level_id']
            level_name = requests[self.request_id]['responses']['Level Name']

            feedback_embed = discord.Embed(
                title=f"**{self.option}**",
                description=f"**Level Name:** {level_name}\n**Level ID:** {level_id}\n\n**Reason:**\n```{reason}```",
                color=discord.Color.green() if self.option == "Sent" else discord.Color.red()
            )
            feedback_embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/816702248242380880.png?v=1" if self.option == "Sent" else "https://cdn.discordapp.com/emojis/816702133625421872.png?v=1")
            feedback_embed.add_field(name="Request Helper", value=self.feedback_author.mention, inline=False)

            # Send the feedback embed to the channel
            await interaction.channel.send(
                content=f"As Requested By: {original_author_mention}",
                embed=feedback_embed
            )
            await interaction.response.send_message("Feedback submitted successfully!", ephemeral=True)
        else:
            await interaction.response.send_message("Request not found.", ephemeral=True)

# Define a view with a dropdown menu for feedback options
class FeedbackView(View):
    def __init__(self, request_id):
        super().__init__()
        self.request_id = request_id
        self.add_item(FeedbackDropdown(request_id))

# Define the dropdown menu
class FeedbackDropdown(Select):
    def __init__(self, request_id):
        self.request_id = request_id
        options = [
            discord.SelectOption(label="Sent", description="Mark the level as sent"),
            discord.SelectOption(label="Not Sent", description="Mark the level as not sent")
        ]
        super().__init__(placeholder="Choose an action...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        option = self.values[0]
        feedback_modal = FeedbackModal(option, self.request_id, interaction.user)
        await interaction.response.send_modal(feedback_modal)

# Command to toggle the required status of a question
@bot.command()
async def modalreq(ctx, question_number: int):
    if 1 <= question_number <= 5:
        required_questions[question_number - 1] = not required_questions[question_number - 1]
        await ctx.send(f"Question {question_number} required status toggled to {required_questions[question_number - 1]}")
    else:
        await ctx.send("Invalid question number. Please provide a number between 1 and 5.")

# Command to create the button
@bot.command()
async def reqbutton(ctx):
    button = Button(label="Request a Level", style=discord.ButtonStyle.primary)

    async def button_callback(interaction: discord.Interaction):
        if requests_open:
            modal = SurveyModal(required_questions)
            await interaction.response.send_modal(modal)
        else:
            await interaction.response.send_message("Requests are currently closed, come back soon!", ephemeral=True)

    button.callback = button_callback

    view = View()
    view.add_item(button)
    await ctx.send("Click the button to request a level.", view=view)

# Command to unlock the requests
@bot.command()
async def requnlock(ctx):
    global requests_open
    requests_open = True
    await ctx.send("Requests have been unlocked.")

# Command to lock the requests
@bot.command()
async def reqlock(ctx):
    global requests_open
    requests_open = False
    await ctx.send("Requests have been locked.")

# Reinitialize feedback views and buttons when the bot restarts
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    for request_id, request_data in requests.items():
        message_id = request_data.get('message_id')
        if message_id:
            channel = bot.get_channel(your_channel_id)  # Replace with your channel ID
            message = await channel.fetch_message(message_id)
            view = FeedbackView(request_id)
            await message.edit(view=view)

# Run the bot
bot.run(DISCORD_TOKEN)
