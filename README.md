# sphinx-bot
Discord bot for the official [*Sphinx and the Cursed Mummy* community](https://discord.gg/sphinx).


## How to use
Make a executable `start-bot.sh` with these contents to run it and log the mirrored output with `tee`.
```bash
export DISCORD_TOKEN='tH15iS4.lEgITtOk3N-P13A5eJUsTU53nnE+1M-W4i7nG.leAkd'
python -u sphinx-bot.py 2>&1 | tee --ignore-interrupts --append discord.out # swy: without the tee «-i» parameter the Ctrl-C python handler won't work while saving the output with «tee»
exit $PIPESTATUS                                                            # swy: $? won't work to retrieve the exit code under «tee»: https://stackoverflow.com/a/1221870/674685
```

You can use something like `tmux` to daemonize it in your server. Good luck.

## Requisites

Python, [discord.py](https://discordpy.readthedocs.io/en/latest/), a chat server, one token and some patience.
