// MoM Server - Modified from FPS Starter Kit
// Loads common module for proper connection handling

// Load up common script base - THIS IS CRITICAL for clientConnection.cs
loadDir("common");

// Set WorldPort default for dedicated server
$Py::WorldPort = "28000";
$Py::TestVar = "SCRIPT_EXECUTED";

// Load defaults
exec("./server/defaults.cs");

// Load preferences
exec("./server/prefs.cs");

// Load server init and start
exec("./server/init.cs");
initServer();
initDedicated();
