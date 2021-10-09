// // REFRESH TIMER
var secs = document.getElementById('timer').innerText;
let refresh_timer = setInterval(count, 1000);

function count(){
    if (secs == 0){
        document.getElementById('refresh').innerText = 'Refreshing...';
        location.reload();
    };

    secs--;
    document.getElementById('timer').innerText = secs;
};

// LOW POWER TOGGLE
document.getElementById('LowPowerModeToggle').addEventListener("change", function (e) {

    var command;

    if (this.checked) {
        command = "lowpower";
    }
    else {
        command = "fullpower";
    };

    let xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function (e) {
        if (xhr.readyState === XMLHttpRequest.DONE) {
            location.reload();
        }
        else {
            console.log("error");
        };
    };

    xhr.open("POST", "/power");
    xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    xhr.send(String.raw`power=${command}`);

});

function reboot() {
    clearInterval(refresh_timer)
    document.getElementById('reboot-body').hidden = true
    document.getElementById('reboot-spinner').hidden = false
}


// REFRESH LINK
function refresh(){
    location.reload();
};