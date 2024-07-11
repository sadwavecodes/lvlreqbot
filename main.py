import os
import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput, Select
import uuid

# Get the token from the environment variable
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Define the bot with the command prefix '!'
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Define a list to keep track of which questions are required
required_questions = [False] * 5

# Define a set to store used Level IDs
used_level_ids = set()

# Define a dictionary to store request details by request ID
requests = {}

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

        if level_id in used_level_ids:
            await interaction.response.send_message(f"Level ID {level_id} has already been used. Please use a unique Level ID.", ephemeral=True)
            return

        used_level_ids.add(level_id)

        # Create an embed with the responses
        request_id = str(uuid.uuid4())
        embed = discord.Embed(title="Request", color=discord.Color.blue())
        embed.set_author(name=f"User ID: {interaction.user.id}", icon_url=interaction.user.avatar.url)

        embed.add_field(name="Level Name", value=self.children[0].value, inline=False)
        embed.add_field(name="Level ID", value=self.children[1].value, inline=False)
        embed.add_field(name="Difficulty", value=self.children[2].value, inline=False)
        embed.add_field(name="Video", value=self.children[3].value, inline=False)
        embed.add_field(name="Note", value=self.children[4].value, inline=False)
        embed.set_footer(text=f"Request ID: {request_id}")

        # Create a button and dropdown menu
        button_view = FeedbackView(request_id)
        message = await interaction.response.send_message(embed=embed, view=button_view)

        # Store the original message ID and author for future reference
        requests[request_id] = {
            'message_id': message.id,
            'author': interaction.user,
            'embed': embed
        }

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
        original_author = requests[self.request_id]['author']
        feedback_embed = discord.Embed(
            title=f"Level {self.option}",
            description=f"Reason:\n```{reason}```",
            color=discord.Color.green() if self.option == "Sent" else discord.Color.red()
        )
        await interaction.response.send_message(
            content=f"{original_author.mention}, {self.feedback_author.mention}",
            embed=feedback_embed
        )

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
        modal = SurveyModal(required_questions)
        await interaction.response.send_modal(modal)

    button.callback = button_callback

    view = View()
    view.add_item(button)
    await ctx.send("Click the button to request a level.", view=view)

# Command to reopen a request by ID
@bot.command()
async def req(ctx, request_id: str):
    if request_id in requests:
        embed = requests[request_id]['embed']
        view = FeedbackView(request_id)
        await ctx.send(embed=embed, view=view)
    else:
        await ctx.send("Invalid request ID. Please provide a valid request ID.")

# Run the bot
bot.run(DISCORD_TOKEN)
