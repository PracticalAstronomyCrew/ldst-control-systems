# ldst-control-systems

## Code Structure:
Start_Telescope.py --> front end packager 
- Uses Multiprocess to launch all below simultaneously
- Currently no possible interaction

Controller.py --> Contains packager class for Telescope and Dome control
- Only function causing the Dome and Telescope to move, all requests must be passed through this function

Checks.py --> Constantly checks the weather and interrupts in case weather is changing for the worse
- In case sunset is not reached modifies powershell script to rerun Start_Telescope.py after sunset

Scheduler.py --> Scheduling application, creates schedule based on priority and then evaluates which observations are suppose to be run