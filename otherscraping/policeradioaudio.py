import asyncio, websockets
import os, sys, json
async def thing():
	async with websockets.connect("ws://waco.myddns.me:55224/Calls") as websocket:
		print(await websocket.recv()) #should be {"Connected": "true"}
		while True:
			resp = json.loads(await websocket.recv()) #will be something like:
			cmd = f"curl waco.myddns.me:55224{resp['AudioFilename']} --output {resp['Frequency']}_{resp['TargetID'].replace('|', '')}.mp3"
			print(cmd)
			os.system(cmd)
		'''
		{"DT_RowId":879874,"Time":"9:51:13 PM",
		"Date":"11/4/2021","TargetID":"60848",
		"TargetLabel":"South Cities 1","TargetTag":"SCPD Disp1",
		"SourceID":"51846","SourceLabel":"","SourceTag":null,"LCN":"101",
		"Frequency":"853.53750","CallAudioType":"Analog","SystemID":"290F",
		"SystemLabel":null,"SystemType":"Motorola","AudioStartPos":0.0,
		"CallDuration":"9.8","AudioFilename":"/media/2021-11-04/60848-South%20Cities%201/2021-11-04_215112_60848-South%20Cities%201_51846-_1_290F.mp3",
		"VoiceReceiver":"SCPD Disp1","SiteID":"1","SiteLabel":null,"CallType":"Group","StartTime":"2021-11-04T21:51:13-07:00"}
		'''
		

asyncio.run(thing())