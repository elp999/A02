import discord
from discord.ext import commands
import ffmpeg

from youtube_dl import YoutubeDL

class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.is_playing = False
        self.is_paused = False
        self.music_queue = []
        self.YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        self.vc = None

    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info("search:%s" % item, download=False)['entries'][0]
            except Exception:
                return False
        return {'source': info['formats'][0]['url'], 'title': info['title']}

    def play_next(self):
        if len(self.music_queue) > 0:
            self.is_playing = True

            m_url = self.music_queue[0][0]['source']

            self.music_queue.pop(0)

            self.vc.play(discord.FFmpegAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next)
        else:
            self.is_playing = False

    async def play_music(self, ctx):
        if len(self.music_queue) > 0:
            self.is_playing = True
            m_url = self.music_queue[0][0]['source']

            if self.vc == None or not self.vc.is_connected():
                self.vc = await self.music_queue[0][1].connect()

                if self.vc == None:
                    await ctx.send("Couldnt join")
                    return
            else:
                await self.vc.move_to(self.music_queue[0][1])

            self.music_queue.pop(0)

            self.vc.play(discord.FFmpegAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next)
        
        else:
            self.is_playing = False
        
    @commands.Cog.listener()
    async def on_ready(self):
        print("Music Cog is ready.")
    
    @commands.command(name="play", aliases=["p"], help="time to get a watch")
    async def play(self, ctx, *args):
        query = "".join(args)

        voice_channel = ctx.author.voice.channel
        if voice_channel is None:
            await ctx.send("connect to a vc")
        elif self.is_paused:
            self.vc.resume()
        else:
            song = self.search_yt(query)
            if type(song) == type(True):
                await ctx.send("not youtube link")
            else:
                await ctx.send("song added to the Louiussy")
                self.music_queue.append([song, voice_channel])

                if self.is_playing == False:
                    await self.play_music(ctx)

    @commands.command(name="pause", help="pauses")
    async def pause(self, ctx, *args):
        if self.is_playing:
            self.is_playing = False
            self.is_paused = True
            self.vc.pause()
        elif self.is_paused:
            self.is_playing = True
            self.is_paused = False
            self.vc.resume()

    @commands.command(name="resume", help="resumes")
    async def resume(self, ctx, *args):
        if self.is_paused:
            self.is_playing = True
            self.is_paused = False
            self.vc.resume()
        elif self.is_paused:
            self.vc.resume()

    @commands.command(name="skip", help="skips")
    async def skip(self, ctx, *args):
        if self.vc != None and self.vc:
            self.vc.stop()
            await self.play_music(ctx)

    @commands.command(name="queue", aliases=['q'], help="shows queue")
    async def queue(self, ctx):
        retVal = ""

        for i in range(0, len(self.music_queue)):
            if i > 10: break
            retVal += self.music_queue[i][0]['title'] + '\n'

        if retVal != "":
            await ctx.send(retVal)
        else:
            await ctx.send("No music in queue")

    @commands.command(name="nuke", aliases=['clear'], help="clears queue")
    async def queue(self, ctx, *args):
        if self.vc != None and self.is_playing:
            self.vc.stop()
        self.music_queue = []
        await ctx.send("Daddy Louie nuked")
    
    @commands.command(name="leave", help="leaves vc")
    async def leave(self, ctx, *args):
        if self.vc != None and self.vc:
            await self.vc.disconnect()
            self.vc = None
            self.is_playing = False
            
    
async def setup(bot):
    await bot.add_cog(music_cog(bot))



#async def load_cogs():
#    await client.load_extension('music_cog')
#
#async def main():
#    await load_cogs()
#    await client.login(TOKEN)
#    await client.connect()

#asyncio.run(main())
