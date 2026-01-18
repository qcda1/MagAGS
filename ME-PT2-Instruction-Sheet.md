# MT-PT2 Instruction Sheet Excerpt
## Introduction
The ME-PT2 (pigtail two-wire) adapter is designed to be connected to Magnum's Auto Generator Start (AGS) controller to allow a connected generator to be started by an external switching device. This is useful in applications where there is a requirement to conveniently and automatically turn the generator on/off externally through a manually controlled switch, or from an automatically controlled switching device.
This adapter has two pigtail wires and when connected together they cause the AGS controller to start and run the connected generator.

> **Info:** The high temperature start feature is not available when using the ME-PT2. However, the low battery voltage start feature is still available.

To install the ME-PT2, refer to the steps below:
1. Connect the two white wires on the ME-PT2 adapter to a two-contact external switching device (i.e., switch).
2. Plug the ME-PT2 adapter into the REMOTE (purple) port on the ME-AGS-N.

> **Info:** The remote temperature sensor that comes with the
ME-AGS-N (normally plugged into the AGS's REMOTE port) is not used when the ME-PT2 is connected.

## Setup
When using the ME-PT2 with the ME-AGS-N, configure the ME-RC (or ME-ARC) to allow the AGS to accept the external input from the ME-PT2.
• Find the temperature start setting-depending on your remote: ME-RC (under AGS/04 Start Temp F menu), or ME-ARC (under SETUP/04E Gen Run Temp/Start menu). Then, select the Start-Ext Input setting.

## ME-ARC
1. Using a momentary type switch: Pressing the switch causes the generator to run for two minutes, and then stop.
2. Using a maintain type switch: If the switch is set to ON, the generator continues to run until the switch is set to OFF. Once the switch is set to OFF, the generator will run for two minutes, and then stop.


> **Info:** In my application, I am using a momentary type switch. When reaching the low SOC level, the relay will switch on for one second to start the generator simulating a momentary switch. The generator will run for the set "Set Gen Run Temp Time" value of 0.5h or 30 minutes.

