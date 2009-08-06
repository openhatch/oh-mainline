if (typeof console == "undefined") {
    console = {};
    console.log = function() {};
    console.debug = function() {};
    console.info = function() {};
}

if (typeof fireunit == "undefined") {
    fireunit = {};
    fireunit.ok = function() {};
    fireunit.testDone = function() {};
}

// Thanks to
// http://stackoverflow.com/questions/237104/javascript-array-containsobj/237176#237176
Array.prototype.contains = function(obj) {
  var i = this.length;
  while (i--) {
    if (this[i] === obj) {
      return true;
    }
  }
  return false;
}

