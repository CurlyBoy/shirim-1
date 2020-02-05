import requests, discord, re, aiohttp, io
from discord.ext import commands
from commands.configuration import users_db, general_error, FMUser
from commands.fm import Scrobbles

def setup(bot):
    bot.add_cog(PersonalChart(bot))

async def charter(ctx, user_id, get=False):
    await ctx.trigger_typing()
    user = users_db.find_one(user_id=user_id)
    
    try:
        chart_url = user["chart_url"]
        if chart_url == "":
            raise Exception
        else:
            embed = discord.Embed().set_image(url=chart_url)
            await ctx.send(content=ctx.author.mention, embed=embed)
    except:
        if get:
            await ctx.send("**Error:** The specified user doesn't seem to have set a chart.")
            return
        await ctx.send("**Error:** You haven't seemed to have set a chart. Use the `submit` command to set one.")

async def profiler(ctx, member, get=False):
    await ctx.trigger_typing()
    user = users_db.find_one(user_id=member.id)

    if user is None:
        return

    try:
        lastfm = user["username"]
    except:
        if get:
            await ctx.send("**Error:** It seems this user doesn't have enough data to generate a profile.")
            return
        await ctx.send("**Error:** It seems you don't have enough data to generate a profile. Use `!set` to set a last.fm name to fix this.")
        return

    scrobbles = Scrobbles(lastfm)
    userobj = FMUser(lastfm)

    recent_scrobble = f"{scrobbles.recent_scrobble.name} - {scrobbles.recent_scrobble.artist}"
    playcount = userobj.playcount
    embed = discord.Embed(
        title=f"{ctx.author.name}#{ctx.author.discriminator}",
        description=f"Total Scrobbles: **{playcount}**",
    )
    embed.set_thumbnail(url=ctx.message.author.avatar_url)
    embed.set_footer(
        text=f"Recently Played: {recent_scrobble}" # my silly little scapegoat for my bad coding
    )
    embed.set_author(
        name=f"last.fm",
        icon_url=userobj.avatar,
        url=scrobbles.user_url
    )
    try:
        rym = user["rym"]
        embed.add_field(
            name="RateYourMusic", value=f"https://rateyourmusic.com/{rym}", inline=False
        )
    except:
        pass
    try:
        spotify = user["spotify"]
        embed.add_field(
            name="Spotify", value=f"https://open.spotify.com/user/{spotify}", inline=False
        )
    except:
        pass
    return embed

class PersonalChart(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def submit(self, ctx, *args):
        await ctx.trigger_typing()
        usage = "usage: `submit <chart url>, or attach a chart as an image`"
        
        if len(args) == 0:
            if len(ctx.message.attachments) != 1:
                await ctx.send(usage)
                return
            
            if ctx.message.attachments[0].height is None:
                await ctx.send("**Error:** You may only attach an image to submit as a chart!")
                await ctx.send("Your chart has been successfully added! You may call it using `chart`.")
            
            try:
                users_db.upsert(dict(user_id=ctx.author.id, chart_url=ctx.message.attachments[0].url), ["user_id"])
                await ctx.send("Your chart has been successfully added! You may call it using `chart`.")
                return
            except:
                await ctx.send(general_error)
                return
        
        elif len(args) >= 1:
            try:
                request = requests.get(url=args[0])
                
                if re.search(r"^(image)", request.headers["Content-Type"]) is None:
                    print("**Error:** The specified URL doesn't seem to link to an image.")
                    return
                
                users_db.upsert(dict(user_id=ctx.author.id, chart_url=args[0]), ["user_id"])
                await ctx.send("Your chart has been successfully added! You may call it using `chart`.")

            except Exception as e:
                await ctx.send("**Error:** The specified URL doesn't seem to be an image.")
                raise e
    
    @commands.command(name="chart")
    async def get_chart(self, ctx):
        await charter(ctx, ctx.author.id, get=False)
    
    @commands.command(name="rmchart")
    async def remove_chart(self, ctx):
        await ctx.trigger_typing()
        try:
            users_db.upsert(dict(user_id=ctx.author.id, chart_url=""), ["user_id"])
            await ctx.send("Your chart has been successfully removed.")
        except Exception as e:
            await ctx.send(general_error)
            return
    
    @commands.command()
    async def setrym(self, ctx, *args):
        await ctx.trigger_typing()
        usage = "usage: `setrym <rym username>`"

        if len(args) == 0:
            await ctx.send(usage)
            return
        
        try:
            users_db.upsert(dict(user_id=ctx.author.id, rym=args[0]), ["user_id"])
            await ctx.send(f"Your RYM username has been successfully set as {args[0]}.")
        except:
            await ctx.send(general_error)
    
    @commands.command()
    async def setspotify(self, ctx, *args):
        await ctx.trigger_typing()
        usage = "usage: `setspotify <spotify username>`"

        if len(args) == 0:
            await ctx.send(usage)
            return

        try:
            users_db.upsert(dict(user_id=ctx.author.id, spotify=args[0]), ["user_id"])
            await ctx.send(f"Your Spotify username has been successfully set as {args[0]}.")
        except:
            await ctx.send(general_error)
    
    @commands.command()
    async def profile(self, ctx):
        profile = await profiler(ctx, ctx.author)
        await ctx.send(content=ctx.author.mention, embed=profile)