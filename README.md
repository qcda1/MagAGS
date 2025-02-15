# MagAGS
External control of Magnum Energy ME-AGS-N module instead of ME-BMK using a Raspberry Pi

**_NOTICE: At the creation of this repository, only the relay.py and manage_gen() parts were tested with the relay board
        in Debian. All tested fine. I'm waiting for the delivery of the ME-PT2. I expect putting this in production
        with the generator in the second half of mars 2025. The repository will be updated accordingly._**

## Introduction
The Magnum Energy inverter/charger line of business is discontinued since september 2024. This means there is no more support. I run a MS4448PAE inverter/charger since 2014 in an offgrid cottage and workshop powered by solar energy. The unit work flawlessly with all sorts of loads. It is also equiped with the ME-AGS-N generator controller to charge batteries from generator power in cloudy months. In october of 2024, I moved from FLA battery bank to LiFePO4 batteries. Since then, the ME-AGS can't use battery voltage to detect time to charge and automatically start the generator. The discharge voltage curve is too flat and the Magnum not accurate enough. So I purchased a BMK (Battery Management Kit) that estimate the battery's SOC (State Of Charge) and allow the AGS to manage the generator use form the % SOC instead of the battery's voltage. Unfortunately, the BMK has the issue where it detect 100% SOC too early in the charging process. For example after a day without sun, the SOC would be at 85% and on a cloudy day with little power, something happen in the BMK making it go at 100%. From that point, there is 15% difference between real battery SOC and what the BMK believe it is at. This is a major issue since the BMK overestimate the SOC meaning that at low SOC, it is possible that the AGS doesn't start the generator when the battery are low... This could potentially drain the battery bank completely or prevent me from using the whole battery's content.
So I found out there was another way of managing the AGS by using the ME-PT2 adaptor that allow an external relay to control the generator. Since my Raspberry Pi track operational parameters of my devices, I have the SOC measured by the Midnite Solar charge controller and the SOC of the battery's BMS. Interfacing a relay to the Raspberry and a few Python programs, I can manage the way I want to control the automatic generator charging process. This repo contain what's required to implement such control.

## Parts list
I use the following:
1. USB dual relay board
2. Raspberry Pi loaded with its OS
3. Magnum ME-AGS-N Auto Generator Start module
4. Magnum ME-PT1 relay connector

## Python
The provided code will allow you to manage the USB relay board from the Raspberry Pi. You will be able to adapt the code to your own environment. In my case for example, I have several Python programs that acquire operational data, store the information in database file and report with a Web user interface. You might have different equipment that require specific programs adapeted to their own communication interfaces and protocol.

To get you going, you will need to get some OS packages and Python modules:

    sudo apt-get update
    sudo apt-get install python-dev libusb-1.0-0-dev libudev-dev
    pip install --upgrade setuptools
    pip install hidapi

To test the setup:
1. Create a directory for the test environment
2. Copy relay.py Python script
3. Plug your dual USB dual relay
4. Run relay.py You should hear and see the relay being switched on and off
5. If all good, you can run manage_gen.py as by default, will simulate the operation
   of a generator autostart when battery SOC goes low.

Once successfully tested, you can implement the manage_gen() function in your system monitoring program
with adequate min and max SOC. In my case, I have a monitoring program that loops throught the inquiries of
my solar energy system such as the two Midnite Solar 150 charge controllers, the Magnum MS4448PAE
inverter/charger and the MapleLeaf Beaver 48VDC/100Ah batteries. From these, I get three measurements of
the SOC. I believe the SOC from the Classic 150 with Whizbang JR is the most accurate so that will be
the lead SOC to manage the generator.

## Wiring diagram
![MagAGS](https://github.com/user-attachments/assets/d9f7bc4a-2950-41c1-9690-f6a1d08e7f2b)
## Pictures:
![RelayBoard](https://github.com/user-attachments/assets/e3c6516a-7ad6-4004-a510-9446ae4cf337)
![RPI4](https://github.com/user-attachments/assets/2c0e2180-4ee7-4a23-ac34-12cacd0f28a9)
![ME-AGS-N](https://github.com/user-attachments/assets/c746d700-a8e7-41e2-983c-d1db98b48d24)
![ME-PT2](https://github.com/user-attachments/assets/4772d69d-8bb8-4bdf-a7c1-061aa648c5bb)

## References
- The above solution is based on the excellent work performed here: https://github.com/jaketeater/Very-Simple-USB-Relay
- USB relay board datasheet: [USBB-RELAY-08(DatasheetFR).pdf](https://github.com/user-attachments/files/18773244/USBB-RELAY-08.DatasheetFR.pdf)
- ME-PT2 connector: [64-0026-Rev-D-ME-PT2_Booklet_Print.pdf](https://github.com/user-attachments/files/18773310/64-0026-Rev-D-ME-PT2_Booklet_Print.pdf)
- 







