###Author: Jonatas Ribeiro Senna Pires
###Date: 29/10/2020
###Language: micropython
###Target: esp32 dev-kit1

from machine import Timer, WDT
import time
import ubinascii
from umqtt.robust import MQTTClient


class Device:
    def __init__(self,number, name, spacelessname, mqttServer, time=30000, WDTTimeout=10000):
        self.basicTopic = 'homie/device'+str(number)+'/'+spacelessname+'/'
        self.number = number
        self.name = name
        self.spacelessname = spacelessname
        self.sendInfoTimer = Timer(0)
        self.WDT = WDT(timeout=WDTTimeout)
        self.setup()
        self.client = MQTTClient(ubinascii.hexlify(machine.unique_id()), mqttServer, keepalive=240)
        self.client.set_last_will(self.basicTopic+'connection', 'CONNECTION ERROR', retain=True)
        self.client.set_callback(self.msgCallBack)
        self.client.connect()
        self.homieSetUp()
        self.subscribe()
        self.sendInfoTimer.init(period = time, mode=Timer.PERIODIC, callback = self.sendInfo)
        self.sendInfo()


    def setup(self):
        self.properties = {'connection':{'value':'Active','settable':True, 'onResetSend':True, 'action':self.msgRecieved}}
        self.subscribeExternal = {}
        self.readFunctions = []

    def msgCallBack(self, topic, msg):
        decodedMsg = msg.decode("utf-8")
        decodedTopic = topic.decode("utf-8")
        if decodedTopic in self.subscribeExternal:
            self.subscribeExternal[decodedTopic]['action'](decodedMsg)
        else:
            property = decodedTopic[len(self.basicTopic):]
            if property in self.properties:
                self.properties[property]['action'](decodedMsg)

    def subscribe(self):
        for property in self.properties:
            if self.properties[property]['settable']:
                print(self.basicTopic+property)
                self.client.subscribe(self.basicTopic+property)
                if not self.properties[property]['onResetSend']:
                    self.client.check_msg()
        for external in self.subscribeExternal:
            print(external)
            self.client.subscribe(external)

    def sendInfo(self,nothing=0):
        self.readInfo()
        #self.client.publish(self.basicTopic + 'conexao', 'Ativa')
        for property in self.properties:
            print(property + ': ' + str(self.properties[property]['value']))
            self.client.publish(self.basicTopic + property, str(self.properties[property]['value']))
        #self.WDT.feed()

    def readInfo(self):
        for function in self.readFunctions:
            function()

    def msgRecieved(self, nothing):
        self.WDT.feed()

    def homieSetUp(self):
        self.client.publish('homie/device' + str(self.number) + '/$homie', '3.0.1')
        self.client.publish('homie/device' + str(self.number) + '/$name', self.name)
        self.client.publish('homie/device' + str(self.number) + '/$state', 'ready')
        self.client.publish('homie/device' + str(self.number) + '/$nodes', self.spacelessname)
        self.client.publish(self.basicTopic + '$name', self.name)
        straux = ''
        for property in self.properties:
            straux += property+','
        straux = straux[:len(straux)-1]
        self.client.publish(self.basicTopic[:len(self.basicTopic) - 1] + '$properties', straux)
        for property in self.properties:
            self.client.publish(self.basicTopic + property + '/$name', property)
            self.client.publish(self.basicTopic + property, str(self.properties[property]['value']))
            self.client.publish(self.basicTopic + property + '/$settable', str(self.properties[property]['settable']).lower())
