// MoM Server Root Bootstrap Script

// Disable DSO caching to avoid stale bytecode issues
$Scripts::ignoreDSOs = true;

echo("#### main.cs starting");

// Parse command line arguments first
$Py::WorldPort = "";
$Server::Dedicated = false;
$zoneArg = "";

for (%i = 1; %i < $Game::argc; %i++)
{
   %arg = $Game::argv[%i];
   %nextArg = $Game::argv[%i+1];

   if (%arg $= "-worldport" && %nextArg !$= "")
      $Py::WorldPort = %nextArg;
   else if (%arg $= "-dedicated")
      $Server::Dedicated = true;
   else if (%arg $= "-world" && %nextArg !$= "")
      $Py::DedicatedWorld = %nextArg;
   else if (%arg $= "-serverport" && %nextArg !$= "")
      $Pref::Server::Port = %nextArg;
   else if (%arg $= "-zone" && %nextArg !$= "")
      $zoneArg = %nextArg;
}

// Set mod paths to game directory
$gameRoot = "minions.of.mirth";
setModPaths($gameRoot);

// Load common module (defines initBaseServer which loads clientConnection.cs)
echo("#### About to exec common/main.cs");
if (!exec("common/main.cs")) {
   echo("#### ERROR: Failed to exec common/main.cs, trying ./common/main.cs");
   exec("./common/main.cs");
}
echo("#### Done with common/main.cs exec attempt");

echo("#### $Pref::Server::Port = " @ $Pref::Server::Port);
echo("#### $zoneArg = " @ $zoneArg);
echo("#### $Py::WorldPort = " @ $Py::WorldPort);

// Initialize Python integration (registers PyExec command)
PyInit();

// Load server init from mod directory
exec("minions.of.mirth/server/init.cs");

// Call init functions
initServer();
if ($Server::Dedicated)
   initDedicated();
