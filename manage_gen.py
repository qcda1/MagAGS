#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Function to perform generator control with a relay board.
# It is meant to be used in a Magnum Energy setup using 
# the ME-AGS-N Auto Generator Start module and the ME-PT1 or ME-PT2 relay connector.
# Uses the HID library instead of usb.
# Uses relay.py to interface with the relay board.
#
from relay import Relay

def manage_gen(SOC, SOC1, SOC2, relay):
    '''
    Function to magange the automatic start/stop of the generator
    based on the supplied range of SOC values.
    SOC = current State of Charge to process
    SOC1 = lower limit SOC value to start the generator
    SOC2 = upper limit SOC value to stop the generator

    This function should be called from the main loop of the program
    that monitors the SOC of the battery bank.

    This function returns the state of the relay: True = on, False = off
    If the difference between SOC1 and SOC2 is less than 5% then return None.
    '''

    if SOC < 0 or SOC > 100: raise Exception("SOC must be between 0 and 100.")
    if SOC1 < 0 or SOC1 > 100: raise Exception("SOC1 must be between 0 and 100.")
    if SOC2 < 0 or SOC2 > 100: raise Exception("SOC2 must be between 0 and 100.")
    if SOC1 > SOC2: raise Exception("SOC1 must be less than SOC2.")
    if SOC2 - SOC1 < 5: raise Exception("SOC window too narrow. Must be over 5%.")

    # The relay will turn on when SOC will go down to SOC1 and turn off when SOC will 
    # go up to SOC2.
    if SOC <= SOC1:
        relay.state(1, on=True)
        return "ON"
    elif SOC >= SOC2:
        relay.state(1, on=False)
        return "OFF"
    else:
        return "MAINTAIN"


# Simulation of the manage_gen function.
if __name__ == '__main__':
    from relay import Relay
    from time import sleep
    # Create a relay object
    relay = Relay(idVendor=0x16c0, idProduct=0x05df)
    print(f"relay={relay}")

    # Starting state
    state = "OFF"
    soc = 100
    resp = "MAINTAIN"

    # Never ending loop to simulate SOC decreasing through time at 1% per iteration
    while True:
        if resp == "OFF":
            soc = soc -1 # Rate of discharge of soc
            state = "OFF"
        elif resp == "ON":
            soc = soc + 3 # Higher rate of charge of soc with the simulated generator
            state = "ON"
        else: # This case would be resp = "MAINTAIN" in which case we don't change the state
              # but maintain rate of change to soc.
            if state == "OFF":
                soc = soc - 1
            else:
                soc = soc + 3

        resp = manage_gen(soc, 20, 40, relay)
        print(f"soc={soc} manage_gen={resp}") 
        sleep(0.5)

