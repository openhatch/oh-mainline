if (typeof console == "undefined")
{
    console = {};
    console.log = function() {};
    console.debug = function() {};
    console.info = function() {};
}
if (typeof fireunit == "undefined")
{
    fireunit = {};
    fireunit.ok = function() {};
    fireunit.testDone = function() {};
}