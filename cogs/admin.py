import os
import asyncio
from datetime import datetime, timedelta

from discord.ext import commands, tasks

STAFF_CHANNEL = int(os.getenv('STAFF_CHANNEL'))
ADMIN_ROLE = int(os.getenv('ADMIN_ROLE'))

def is_admin(ctx):
    if ctx.author.id == 173123135321800704: 
        return True
    return ctx.author.has_role("Staff")

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.recruitTask.start()
    
    @commands.command(name = "reload", hidden = True)
    @commands.is_owner()
    async def _reload(self, ctx, ext: str):
        try:
            self.bot.reload_extension("cogs." + ext)
            print("\nReloaded {} extension".format(ext))
        except Exception as e:
            print("Failed to reload {} extension\n".format(ext))
            print(e)
            print("\n")

    @commands.command(name = "shutdown", hidden = True)
    @commands.is_owner()
    async def _shutdown(self, ctx):
        exit()

    @commands.command(aliases = ["addrole"])
    @commands.check(is_admin)
    async def addrank(self, ctx, *args):
        '''Create a new role'''

        roleQuery = " ".join(args)
        member = ctx.author
        roles = member.guild.roles

        for role in roles[1:]:
            if role.name.lower() == roleQuery.lower():
                await self.send_message(ctx.channel, "{} Role **{}** already exists".format(member.mention, role.name))
                return

        await member.guild.create_role(name = roleQuery, reason = "Created role through .addrank")
        await self.send_message(ctx.channel, "{} Created role **{}**".format(member.mention, roleQuery))

    @commands.command(aliases = ["removerole"])
    @commands.check(is_admin)
    async def removerank(self, ctx, *args):
        '''Remove an existing role'''

        roleQuery = " ".join(args)
        member = ctx.author
        roles = member.guild.roles

        for role in roles[1:]:
            if role.name.lower() == roleQuery.lower():
                if not (role.colour.value == 0):
                    await self.send_message(ctx.channel, "{} **{}** is a reserved role".format(member.mention, role.name))
                    return

                await role.delete(reason = "Removed role through .removerank")
                await self.send_message(ctx.channel, "{} Removed role **{}**".format(member.mention, role.name))
                return

        await self.send_message(ctx.channel, "{} Role **{}** doesn't exist".format(member.mention, roleQuery))

    @commands.command()
    @commands.check(is_admin)
    async def recruitpost(self, ctx):
        """Return or overwrite the recruitment post
        
        Usage:
            .recruitpost   
            -- Output contents of resources/recruit_post.md
            .recruitpost <<with attached file called recruit_post.md>>
            -- Overwrites resources/recruit_post.md, a backup is saved as resources/recruit_post.bak"""

        attachments = ctx.message.attachments

        if attachments == []:
            recruitPost = open('resources/recruit_post.md', 'r').read()
            introString = "Post recruitment on https://www.reddit.com/r/FindAUnit"
            outString = "{}\n```{}```".format(introString, recruitPost)

            await self.send_message(ctx.channel, outString)
        else:
            newRecruitPost = attachments[0]
            if newRecruitPost.filename == "recruit_post.md":
                try:
                    os.remove("resources/recruit_post.bak")
                except FileNotFoundError as e:
                    print("No recruit_post.bak exists, can't remove")

                try:
                    os.rename("resources/recruit_post.md", "resources/recruit_post.bak")
                except FileNotFoundError as e:
                    print("No recruit_post.md exists, can't backup")

                await newRecruitPost.save("resources/recruit_post.md")
                await self.send_message(ctx.channel, "{} {}".format(ctx.author.mention, "Recruitment post has been updated"))
                return
            else:
                await self.send_message(ctx.channel, "{} {}".format(ctx.author.mention, "File must be called recruit_post.md"))
                return

    
    #===Utility===#

    async def send_message(self, channel, message: str):
        """Send a message to the text channel"""

        await channel.trigger_typing()
        newMessage = await channel.send(message)

        return newMessage

    async def recruitmentPost(self):
        channel = self.bot.get_channel(STAFF_CHANNEL)
        recruitPost = open('resources/recruit_post.md', 'r').read()
        introString = "Post recruitment on https://www.reddit.com/r/FindAUnit"
        outString = "<@&{}> {}\n```{}```".format(ADMIN_ROLE, introString, recruitPost)

        await self.send_message(channel, outString)
    
    #===Tasks===#

    @tasks.loop(hours = 24)
    async def recruitTask(self):
        targetDays = [0, 2, 4] #Monday, Wednesday, Friday

        now = datetime.utcnow()
        #now = datetime(2020, 4, 22) #A wednesday
        if now.weekday() in targetDays:
            await self.recruitmentPost()

    @recruitTask.before_loop
    async def before_recruitTask(self):
        targetHour = 17
        targetMinute = 0
        
        now = datetime.utcnow()
        #now = datetime(now.year, now.month, now.day, 16, 59, 55)
        future = datetime(now.year, now.month, now.day, targetHour, targetMinute)

        if now.hour >= targetHour and now.minute > targetMinute:
            future += timedelta(days = 1)

        await asyncio.sleep((future - now).seconds)
        

def setup(bot):
    bot.add_cog(Admin(bot))