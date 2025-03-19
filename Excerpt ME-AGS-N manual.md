# Excerpt from the ME-AGS-N user manual
## SETUP: 04E Gen Run Temp Menu
This menu allows you to set and enable a temperature value that will automatically start the generator — typically to power an air conditioner for cooling — based on an increase in temp, or by using an A/C thermostat control.

>**Info:** The optional ME-PT1 or ME-PT2 pigtail adapters can be used to connect an A/C or relay control circuit. For more information, refer to the instruction sheet for each pigtail adapter (part number 64- 0025 for ME-PT1 instructions, or 64-0026 for ME-PT2 instructions).

>**Info:** This temperature autostart feature requires that the AGS’s remote temp sensor cable (Figure 1-2) or an optional ME-PT1 or ME- PT2 pigtail adapter be connected to the AGS’s REMOTE port (Figure 2-3). When using the remote temperature sensor, the location of the temperature sensor determines the area being monitored for temperature.

### • Set Gen Run Temp Start
– This menu is used to enable and set the temperature that triggers a generator autostart.

**65F - 95F (18C - 35C)** – These settings determine the rising tempera- ture value that triggers a generator temperature autostart.

**Ext Input** – This setting is used when an optional pigtail adapter (ME- PT1, or ME-PT2) is used. When an AGS pigtail adapter is connected to the AGS’s REMOTE port, an external command — either from a thermostat connection on an air conditioner control circuit or an external relay control circuit — is recognized and causes the generator to start.

**Default setting:** Set Gen Run Temp Start = OFF

**Range:** OFF, Ext Input, 65F - 95F or 18C - 35C (5 deg. increments)

>**Info:** If the temperature start feature is not needed, ensure this setting is set to the OFF position.

### • Set Gen Run Temp Time
– This menu sets the amount of time the generator runs after a temperature autostart.

**Default setting:** Set Gen Run Temp Time = 2.0 Hrs

**Range:** 0.5 - 25.5 Hrs (0.5 hr increments)
When the temperature around the remote temp sensor (per the METER: 03D AGS Temp display) increases to the Gen Run Temp Start setting, the generator immediately starts and runs based on the Gen Run Temp Time setting. When this run time period is finished, the temp sensor reading is checked. If the temperature sensor (or thermostat control – if using the optional pigtail adapter) reading is below the Gen Run Temp Start setting, the generator will autostop. If the temperature sensor (or thermostat control) reading is above the Gen Run Temp Start setting, the generator will continue to run for a second run time period. At the end of this second run time period, the temperature sensor reading (or thermostat control) is checked again. This cycle continues as long as the CTRL: 03 Gen Control menu is set to AUTO, or the SETUP: 04F Max Gen Run Time setting is reached, whichever occurs first.

**Why should I use Gen Run Temp?** Typically, in a mobile application such as in an RV or on a boat where the air conditioning (A/C) unit is too much power for the inverter to run from the batteries, this feature is used to start a generator to run the A/C unit. Many RV and marine customers travel with pets and they do not want to leave the pets inside on a hot day. With this feature, you could set the A/C unit to turn on and leave. Whenever the inside temperature rises to the start setting, the generator autostarts to provide power to the A/C unit. This would keep the area cool and comfortable – plus, while the generator is on, the inverter batteries are being charged.

**Where should I set Gen Run Temp Start?** If using this feature to power an A/C unit, the Gen Run Temp Start setting should be slightly above the temperature setting of the thermostat controlling the air conditioner unit. Once the Gen Run Temp Start setting is reached, the gen starts providing power to the A/C unit. The reason the Gen Run Temp Start is set above the A/C unit’s thermostat setting is to ensure the A/C unit runs when the genera- tor starts. If the Gen Run Temp Start setting is below that of the A/C unit’s thermostat setting, the generator runs but the A/C unit is not calling for a run period or cooling. In other words, your generator is running but the pow- er is not being used by the A/C unit – resulting in wasted fuel and run time.

>**Info:** If using the temperature autostart feature to start a generator that is powering two air conditioners, it is suggested that the second air conditioner’s thermostat be set 2° to 5° higher than the first air conditioner. This staggered setting allows the first air conditioner to start and run in an effort to keep the coach cool. If the temperature continues to rise inside the coach, the second air conditioner turns on.

**How long should I set the Gen Run Temp Time?** When using the tem- perature autostart feature, the generator autostarts and runs until the Gen Run Temp Time setting or the SETUP: 04F Max Gen Run Time setting is reached, whichever occurs first. This means you could set the time to the lowest time setting (0.5 Hrs), knowing the generator will attempt to run until the temperature setting is met.
