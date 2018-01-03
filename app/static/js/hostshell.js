$(document).ready(function() {
  $("#loadIcon").hide();
});
// https://javascript.info/keyboard-events
cmdInput.onkeypress = handle;

var cmdHistory = [];
var counterHistory = 0;
var mode = '';
var url = '';
var encstr = '';
var str = '';
var loc = '';

function handle(e) {
  // Supports submitting on Enter key or '?'
  if ((e.code == 'Enter') || (e.code == 'NumpadEnter') || (e.code == 'Slash' && e.shiftKey)) {
    str = document.getElementById('cmdInput').value;

    // Check needed if user enters "conf..." command, as entering config mode will not work with non-config send_command in netmiko
    if (((e.code == 'Enter') || (e.code == 'NumpadEnter')) && (str.substring(0, 4).toLowerCase() == 'conf')) {
      // Toggle config mode checkbox
      document.getElementById('chkConfigMode').checked = true;
      // Toggle config mode
      toggleConfigMode();
    } else if (((e.code == 'Enter') || (e.code == 'NumpadEnter')) && (str.toLowerCase() == 'end')) {
      // Toggle config mode checkbox
      document.getElementById('chkConfigMode').checked = false;
      // Toggle config mode
      toggleConfigMode();
    }
    // Otherwise it's safe to execute all other commands
    else {
      // Do only if cmd box is not empty or contains just a single '?'
      if ((str) || (e.code == 'Slash' && e.shiftKey)) {
        $("#loadIcon").show();

        // Replace '/' with '_'
        // '/' doesn't get encoded in 'encodeURI'
        newstr = str.replace(/\//g, '_');
        encStr = encodeURI(newstr);

        // '?' isn't included in getElementById value, nor is it encoded, so the encoded value for '?' has to be manually entered if it was inputted by the user
        if (e.code == 'Slash' && e.shiftKey) {
          encStr = encStr + '%3F';
        }

        // Pull host ID from URL
        loc = location.href.substr(location.href.lastIndexOf('/') + 1);

        if (document.getElementById("chkConfigMode").checked) {
          mode = 'c';
        } else {
          mode = 'e';
        }
        url = '/hostshelloutput/' + loc + '/' + mode + '/' + encStr;

        $.get(url, function(my_var) {
          $('#outputID').prepend(my_var);
          $("#loadIcon").hide();
          // Erase input box once submitted
          if ((e.code == 'Enter') || (e.code == 'NumpadEnter')) {
            document.getElementById('cmdInput').value = "";
          }
          // If command submitted on '?' press, strip '?' and leave command in input box
          else {
            str = str.replace(/\?/g, '');
            document.getElementById('cmdInput').value = str;
          }
        });
      } else {
        console.log('Textbox is empty') // Debugging purposes only
      }
    }

    // If Enter key pressed, store command in variable, to be used for history (up arrow)
    if ((e.code == 'Enter') || (e.code == 'NumpadEnter')) {
      // Only store command if not empty/blank
      // This checks if string is empty/null, OR contains just whitespace
      if ((str) && !(!str.replace(/\s/g, '').length)) {
        cmdHistory.push(str);
        counterHistory = cmdHistory.length;
        document.getElementById('cmdInput').value = "";
      }
    }
  }
}

// If up arrow pressed, retrieve previous commands entered
cmdInput.onkeydown = checkKey;

function checkKey(e) {
  e = e || window.event;
  // 37 = left
  // 38 = up
  // 39 = right
  // 40 = down
  if (e.keyCode == '38') {
    console.log("ArrowUp");
    counterHistory--;
    // If up key pressed, display previous commands until original one shown.  Don't continue past, or it shows 'undefined'
    if (counterHistory >= 0) {
      document.getElementById('cmdInput').value = cmdHistory[counterHistory];
    } else {
      counterHistory = 0;
    }
  } else if (e.keyCode == '40') {
    console.log("ArrowDown");
    counterHistory++;
    // If down key pressed, cycle through commands until the end.  Don't display anything if nothing left
    if (counterHistory < cmdHistory.length) {
      document.getElementById('cmdInput').value = cmdHistory[counterHistory];
    }
    // If down key pressed after last previous command was shown, display blank form again
    else if (counterHistory >= cmdHistory.length) {
      document.getElementById('cmdInput').value = "";
      counterHistory = cmdHistory.length;
    }
  }
}

function toggleConfigMode() {
  // Pull host ID from URL
  var loc = location.href.substr(location.href.lastIndexOf('/') + 1);

  if (document.getElementById("chkConfigMode").checked) {
    var url = '/enterconfigmode/' + loc;
    $.get(url);
  } else {
    var url = '/exitconfigmode/' + loc;
    $.get(url);
  }
}
