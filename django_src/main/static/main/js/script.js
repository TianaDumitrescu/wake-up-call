const createAlarmBtn = document.getElementById("createAlarmBtn");
const closeBtn = document.getElementById("closeModal");
const alarmCreation = document.getElementById("alarmCreation");

// Open popup
createAlarmBtn.addEventListener("click", () => {
    alarmCreation.style.display = "flex";
});

// Close popup
closeBtn.addEventListener("click", () => {
    alarmCreation.style.display = "none";
});
