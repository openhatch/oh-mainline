if (typeof QUnit == 'undefined') {
    console.log('QUnit not imported.');
}

QUnitRunner = {};
QUnitRunner.ok = function(bool, message) {
    var bool = !!bool;
    if (typeof prefix == 'undefined') { var prefix = ""; }
    test(prefix, function() { ok(bool, message); });
};
QUnitRunner.compare = function(a, b, message) {
    if (typeof prefix == 'undefined') { prefix = ""; }
    test(prefix, function() { equals(a, b, message); });
};
QUnitRunner.testDone = function() {};

StupidRunner = {};
StupidRunner.ok = function(bool, message) {
    var bool = !!bool; //FIXME: Doesn't work in constructive logic.
    if (!bool) { alert("Failed:" + message); }
};
StupidRunner.compare = function(a, b, message) {
    if (a !== b) { alert("Failed: " + a + " != " + b + "; " + message); }
};
StupidRunner.testDone = function() {};

// Pick a test runner here
tester = fireunit;
//tester = QUnitRunner;
//tester = StupidRunner;
