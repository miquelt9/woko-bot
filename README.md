# Woko bot
Finding a place to stay is not easy and if you are thinking in Zürich (Switzerland), the **prices go crazy**. Fortunately there's a good option for local students (e.g.: ETH) and people willing to stay in Zürich during the summer [Woko](https://www.woko.ch/).       
      
However, it is still a quite competitive place to get a room. That's the reason I decided to develop this little Telegram bot that will notify you whenever a [room in Zürich](https://www.woko.ch/en/zimmer-in-zuerich) is available, so **you can be the first** person to contact.       
      
As this project was develop for a friend of mine whose name starts with R, it is no longer hosted. So here are the steps to follow if you wanna get it for you:     

1. Get a VPS or computer that runs 24/7:
2. Create a file named `token.txt` with your Telegram Bot token get it [here](https://core.telegram.org/bots/tutorial).
3. Upload all the files (`token.txt`, `requirements.txt`, `woko_bot.py`)
4. Ensure python is installed and run:
```
pip install -r requirements.txt
python3 woko_bot.py &
```
5. Done!

