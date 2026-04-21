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

const gameMessage = document.getElementById("game-message");
const starterSection = document.getElementById("starter-section");
const partySection = document.getElementById("party-section");
const collectionSection = document.getElementById("collection-section");
const battleSection = document.getElementById("battle-section");
const levelupSection = document.getElementById("levelup-section");

const nextButton = document.getElementById("next-button");
const partyButton = document.getElementById("party-button");
const collectionButton = document.getElementById("collection-button");
const battleButton = document.getElementById("battle-button");

let selectedParty = [];

// Helper function to get CSRF token from cookies, which is needed for POST requests to the Django backend
function getCookie() {
    const name = "csrftoken";
    const cookies = document.cookie.split(";"); // splits the cookie string into an array of individual cookies

    // Iterates through the cookies to find the one with the specified name and returns its value    
    for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.startsWith(name + "=")) {
            return cookie.substring(name.length + 1);
        }
    }
    return "";
}

function showGameMessage(message) {
    gameMessage.textContent = message;
}

function clearGameMessage() {
    gameMessage.textContent = "";
}

function clearSections() {
    starterSection.innerHTML = "";
    partySection.innerHTML = "";
    collectionSection.innerHTML = "";
    battleSection.innerHTML = "";
    levelupSection.innerHTML = "";

    nextButton.style.display = "none";
    partyButton.style.display = "none";
    collectionButton.style.display = "none";
    battleButton.style.display = "none";

    partyButton.textContent = "Show Party";
    collectionButton.textContent = "Show Collection";
}

function mainHub() {
    clearSections();
    clearGameMessage();
    partyButton.style.display = "inline-block";
    collectionButton.style.display = "inline-block";
    battleButton.style.display = "inline-block";
}


function getLucidImage(speciesId) {
    return `/static/main/images/lucids/${speciesId}.png`;
}

/*====================================*/
/*== CHOOSING STARTER FUNCTIONALITY ==*/
/*====================================*/

async function loadStarterData() {
    clearSections();
    clearGameMessage();

    const hasBattle = await checkForActiveBattle();
    if (hasBattle) {
        return;
    }

    try {
        const response = await fetch("/game/starter/"); // makes a GET request to the backend to retrieve starter data from the game app
        const data = await response.json(); // converts that data received from the backend into a JavaScript object

        // If the player has already chosen a starter, then go straight to the main hub of the game
        if (data.starter_chosen) {
            mainHub();
        } else {
            showStarterOptions(data.options); // if player hasn't chosen a starter, calls this function that shows starters to user's screen
        }

    } catch (error) {
        showGameMessage("Could not load data, please reload page");
        console.log(error);
    }
}

function showStarterOptions(options) {
    let html = "<h4>Choose Your Starter</h4>";

    // Loops through the options through the fetch to the backend and creates a div for each starter with its name, type, description, and a button to choose it
    for (let i = 0; i < options.length; i++) {
        const lucid = options[i];
        html += `
            <div class="lucid-div">
                <img src="${getLucidImage(lucid.id)}" alt="${lucid.name}" width="100">
                <div class="lucid-info">
                    <p class="lucid-name"><strong>${lucid.name}</strong></p>
                    <p>Type: ${lucid.type.join(", ")}</p>
                    <p>${lucid.description}</p>
                    <button onclick="chooseStarter(${lucid.id})">Choose</button>
                </div>
            </div>
        `;
    }

    starterSection.innerHTML = html;
}

// Fires off when user clicks the "Choose" button for a starter
async function chooseStarter(speciesId) {
    try {
        // Different then the GET fetch to the backend, this is a POST request that sends 
        // the speciesId of the starter the user chose to the backend so it can be saved in the database
        const response = await fetch("/game/starter/choose/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie() // Have to have a csrftoken for POST requests to django backend
            },
            body: JSON.stringify({
                species_id: speciesId
            })
        });

        const data = await response.json();

        // If the response from the backend is not ok, it means there was an error with choosing the starter, so we show an error message to the user
        if (!response.ok) {
            showGameMessage("Could not choose starter.");
            return;
        }

        starterSection.innerHTML = ""; // Clears the starter options from the screen after user chooses a starter
        showGameMessage(`Starter chosen successfully, you chose ${data.starter.name}!!!!`);
        nextButton.style.display = "inline-block"; // Shows the "Next" button that allows user to continue to the main hub of the game after choosing a starter
    } 
    // If there's an error with the fetch request to the backend
    catch (error) {
        showGameMessage("Something went wrong while choosing starter, please reload page");
        console.log(error);
    }
}

/*============================================*/
/*== SHOWING PARTY/COLLECTION FUNCTIONALITY ==*/
/*============================================*/

// Loaded on the mainHub(), this function is responsible for loading the user's party data from the backend and displaying it on the screen, 
// as well as allowing the user to show/hide their party and collection
async function loadParty() {
    try {
        // Gets the user's party data from the backend with using a GET request
        const response = await fetch("/game/party/");
        const data = await response.json();

        // Gives the current party of the user from the backend and set it in the frontend
        setSelectedPartyFromCurrentParty(data.party); 

        showLevelUpOptions(data.party);


        if (partyButton.textContent === "Show Party") {
            showParty(data.party);
            partyButton.textContent = "Hide Party";
        } else {
            partySection.innerHTML = "";
            partyButton.textContent = "Show Party";
        }
    } catch (error) {
        showGameMessage("Could not load party.");
        console.log(error);
    }
}

// Very similar functionality to loadParty(), but instead for the user's overall lucid collection
async function loadCollection() {
    try {
        const response = await fetch("/game/collection/");
        const data = await response.json();

        if (collectionButton.textContent === "Show Collection") {
            showCollection(data.collection);
            collectionButton.textContent = "Hide Collection";
        } else {
            collectionSection.innerHTML = "";
            collectionButton.textContent = "Show Collection";
        }
    } catch (error) {
        showGameMessage("Could not load collection.");
        console.log(error);
    }
}

// Called by loadParty(), allows user to see the data from the backend about their party
function showParty(party) {
    let html = "<h4>Your Party</h4>";

    // Should never happen that party is null because we create a party for the user when they register,
    // but just in case we check if it's empty and show a message to the user if they don't have any Lucids in their party yet
    if (party.length === 0) {
        html += "<p>You do not have any Lucids in your party yet.</p>";
        partySection.innerHTML = html;
        return;
    }

    // Loops through each lucid in the user's party
    for (let i = 0; i < party.length; i++) {
        const lucid = party[i];

        html += `
            <div class="lucid-div">
                <img src="${getLucidImage(lucid.species_id)}" alt="${lucid.name}" width="100">
                <div class="lucid-info">
                    <p class="lucid-name"><strong>${lucid.name}</strong></p>
                    <p>Level: ${lucid.level}</p>
                    <p>Types: ${lucid.types.join(", ")}</p>
                    <p>HP: ${lucid.current_hp}/${lucid.stats.hp}</p>
                    <p>Attack: ${lucid.stats.attack}</p>
                    <p>Speed: ${lucid.stats.speed}</p>
                    <p>Party Slot: ${lucid.party_slot}</p>
                    <button onclick="removeFromParty(${lucid.owned_id})">Remove from Party</button>
                </div>
            </div>
        `;
    }

    partySection.innerHTML = html;
}

// Very similar to showParty(), but instead for showing the user's overall collection of Lucids instead of just the ones in their party
function showCollection(collection) {
    let html = "<h4>Your Collection</h4>";

    // Should also never happen, but just incase
    if (collection.length === 0) {
        html += "<p>You do not own any Lucids yet.</p>";
        collectionSection.innerHTML = html;
        return;
    }

    for (let i = 0; i < collection.length; i++) {
        const lucid = collection[i];
        const alreadyInParty = selectedParty.includes(lucid.owned_id);

        html += `
            <div class="lucid-div">
                <img src="${getLucidImage(lucid.species_id)}" alt="${lucid.name}" width="100">
                <div class="lucid-info">
                    <p class="lucid-name"><strong>${lucid.name}</strong></p>
                    <p>Level: ${lucid.level}</p>
                    <p>Types: ${lucid.types.join(", ")}</p>
                    <p>HP: ${lucid.current_hp}/${lucid.stats.hp}</p>
                    <p>Attack: ${lucid.stats.attack}</p>
                    <p>Speed: ${lucid.stats.speed}</p>
                    <button onclick="addToParty(${lucid.owned_id})" ${alreadyInParty ? "disabled" : ""}>
                        ${alreadyInParty ? "Already in Party" : "Add to Party"}
                    </button>
                </div>
            </div>
        `;
    }

    collectionSection.innerHTML = html;
}

/*=================================*/
/*== EDITING PARTY FUNCTIONALITY ==*/
/*=================================*/

// Puts the user's party data from the backend into this selectParty variable in the frontend, so we can easily manipulate it in UI
function setSelectedPartyFromCurrentParty(party) {
    selectedParty = [];

    for (let i = 0; i < party.length; i++) {
        selectedParty.push(party[i].owned_id);
    }
}

// Called when the user clicks the "Add to Party" button on a specific lucid in their collection
function addToParty(ownedId) {
    // Checks if that lucid is already in the user's party
    if (selectedParty.includes(ownedId)) {
        showGameMessage("That Lucid is already in your party.");
        return;
    }

    // Party can't be greater than 3
    if (selectedParty.length >= 3) {
        showGameMessage("Your party can only have 3 Lucids.");
        return;
    }

    // If the lucid isn't already in the party and party isn't full, then we add it to the selectedParty variable in the frontend and call saveParty() to update the backend with the new party data
    selectedParty.push(ownedId);
    saveParty();
}

// Called when the user clicks the "Remove from Party" button on a specific lucid in their party
function removeFromParty(ownedId) {
    // We filter out that lucid from the selectedParty variable in the frontend and then call saveParty() to update the backend with the new party data
    selectedParty = selectedParty.filter(id => id !== ownedId);
    saveParty();
}

// This function is responsible for sending the updated party data from the frontend to the backend to be saved in the database
async function saveParty() {
    try {
        // Uses a POST request to send the selectedParty data from the frontend to the backend
        const response = await fetch("/game/party/set/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie()
            },
            body: JSON.stringify({
                owned_lucid_ids: selectedParty
            })
        });

        const data = await response.json();

        // If the response from the backend is not ok, it means there was an error with saving the party, so we show an error message to the user
        if (!response.ok) {
            showGameMessage(data.error || "Could not save party.");
            return;
        }

        // Updates the party shown on the frontend as well
        showGameMessage("Party updated successfully.");
        showParty(data.party);
        partyButton.textContent = "Hide Party";
        loadCollection();
    } catch (error) {
        showGameMessage("Something went wrong while saving party.");
        console.log(error);
    }
}

/*============================*/
/*== LEVEL UP FUNCTIONALITY ==*/
/*============================*/

// This function is responsible for showing the level up options to the user for any Lucids in their party that have pending level ups, 
// and allowing the user to choose which stat they want to increase for each level up
function showLevelUpOptions(party) {
    let html = "<h4>Level Up Your Lucids</h4>";

    let hasPendingLevelups = false;

    for (let i = 0; i < party.length; i++) {
        const lucid = party[i];

        if (lucid.pending_levelups > 0) {
            hasPendingLevelups = true;

            html += `
                <div class="lucid-div">
                    <img src="${getLucidImage(lucid.species_id)}" alt="${lucid.name}" width="100">
                    <div class="lucid-info">
                        <p class="lucid-name"><strong>${lucid.name}</strong></p>
                        <p>Level: ${lucid.level}</p>
                        <p>Pending Level Ups: ${lucid.pending_levelups}</p>
                        <button onclick="applyLevelChoice(${lucid.owned_id}, 'hp')">Increase HP</button>
                        <button onclick="applyLevelChoice(${lucid.owned_id}, 'attack')">Increase Attack</button>
                        <button onclick="applyLevelChoice(${lucid.owned_id}, 'speed')">Increase Speed</button>
                    </div>
                </div>
            `;
        }
    }

    if (!hasPendingLevelups) {
        levelupSection.innerHTML = "";
        return;
    }

    levelupSection.innerHTML = html;
}

// Called when the user clicks on of the "Increase HP/Attack/Speed" buttons for a lucid that has pending level ups, this function sends the user's choice for which stat to increase to the backend to update the lucid's stats in the database
async function applyLevelChoice(ownedLucidId, statChoice) {
    try {
        // Uses a POST request to send the user's choice for which stat to increase
        const response = await fetch("/game/level-up/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie()
            },
            body: JSON.stringify({
                owned_lucid_id: ownedLucidId,
                stat_choice: statChoice
            })
        });

        const data = await response.json();

        if (!response.ok) {
            showGameMessage(data.error || "Could not apply level up.");
            return;
        }

        showGameMessage(`${data.lucid.name} leveled up.`);
        loadParty();
        loadCollection();
    } catch (error) {
        showGameMessage("Something went wrong while leveling up.");
        console.log(error);
    }
}

/*======================*/
/*== BATTLING SYSTEM  ==*/
/*======================*/

// Fired when the user presses the "start battle" button
async function startBattle() {
    try {

        // Uses a POST request to send backend info about a battle starting
        const response = await fetch("/game/battle/start/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie()
            }
        });


        const data = await response.json();
        if (!response.ok) {
            showGameMessage(data.error || "Could not start battle.");
            return;
        }

        showGameMessage("Battle started!");
        showBattle(data.battle);
    } catch (error) {
        showGameMessage("Something went wrong while starting battle.");
        console.log(error);
    }
}

// Called by startBattle(), shows the user the UI for the battle
function showBattle(battle) {
    clearSections();
    let activeLucid = null;

    // Loops through the user's party to find which lucid is currently active in the battle (the one the user is currently controlling in the battle)
    for (let i = 0; i < battle.party.length; i++) {
        if (battle.party[i].is_active) {
            activeLucid = battle.party[i];
            break;
        }
    }

    let attackButtons = "";
    let switchButtons = "";


    // Loops through the types of attacks that the active lucid has and creates a button for each one that allows the user to choose that attack in battle
    for (let i = 0; i < activeLucid.types.length; i++) {
        attackButtons += `
            <button onclick="fight(${i})">${activeLucid.types[i]}</button>
        `;
    }

    // Used as a just in case measure if there were no active lucid found in the user's party for some reason, which should never happen, 
    // but if it does we just show a message to the user and don't show the battle UI since it wouldn't work without an active lucid
    if (!activeLucid) {
        battleSection.innerHTML = "<p>No active Lucid found.</p>";
        return;
    }

    // Loops through the user's party to find any lucids that are not active but also not fainted,
    // which means they are eligible to be switched into battle, and creates a button for each one to allow the user to switch to that lucid in battle  
    for (let i = 0; i < battle.party.length; i++) {
        const lucid = battle.party[i];

        if (!lucid.is_active && !lucid.is_fainted) {
            switchButtons += `
                <button onclick="switchLucid(${lucid.owned_id})">
                    Switch to ${lucid.name}
                </button>
            `;
        }
    }



    let middleSection = "";
    // If the battle is currently in the "awaiting_switch" status, it means the user has just had their active lucid fainted 
    // and now they have to choose which lucid to switch into battle, so we only show the switch buttons and not the attack or run options
    if (battle.status === "awaiting_switch") {
        middleSection = `
            <p><strong>Choose a Lucid to switch to</strong></p>
            ${switchButtons}
        `;
    } else {
        middleSection = `
            <p><strong>Battle</strong></p>
            ${attackButtons}
            ${switchButtons}
            <button onclick="runBattle()">Run</button>
        `;
    }

    nextButton.style.display = "none";
    partyButton.style.display = "none";
    collectionButton.style.display = "none";
    battleButton.style.display = "none";

    let html = `
        <div class="battle-layout">
            <div class="battle-lucid">
                <p class="battle-name"><strong>${activeLucid.name}</strong></p>
                <img src="${getLucidImage(activeLucid.species_id)}" alt="${activeLucid.name}" width="120">
                <p>HP: ${activeLucid.current_hp}/${activeLucid.stats.hp}</p>
            </div>

            <div class="battle-middle">
                ${middleSection}
            </div>

            <div class="battle-lucid">
                <p class="battle-name"><strong>${battle.enemy.name}</strong></p>
                <img src="${getLucidImage(battle.enemy.species_id)}" alt="${battle.enemy.name}" width="120">
                <p>HP: ${battle.enemy.current_hp}/${battle.enemy.stats.hp}</p>
            </div>
        </div>

        <div id="battle-log"></div>
    `;

    html += "<div id='battle-log'></div>";

    battleSection.innerHTML = html;

    // Shows the battle log to the user, which gives a play by play of the battle actions that have happened so far
    showBattleLog(battle.log);
}

// When the user first loads the game, we want to check if they have an active battle in progress that they need to resume, 
// and if so we show them the battle UI instead of the starter options or main hub
async function checkForActiveBattle() {
    try {
        // Uses a GET request to see if there is a current battle in the backend for that user
        const response = await fetch("/game/battle/");
        const data = await response.json();

        // If so, then we will resume the battle, by calling showBattle()
        if (response.ok) {
            showGameMessage("Resuming your battle.");
            showBattle(data.battle);
            return true;
        }

        return false;
    } catch (error) {
        console.log(error);
        return false;
    }
}

// Called when the user clicks one of the attack buttons in battle, this function sends the user's choice for which attack to use to the backend, which then processes that attack and returns the updated battle data to be shown in the frontend
async function fight(attackTypeIndex) {
    try {
        // Uses POST request to send the user's attack choice to the backend
        const response = await fetch("/game/battle/fight/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie()
            },
            body: JSON.stringify({
                attack_type_index: attackTypeIndex
            })
        });

        const data = await response.json();

        if (!response.ok) {
            showGameMessage(data.error || "Could not attack.");
            return;
        }

        handleBattleResult(data);
    } catch (error) {
        showGameMessage("Something went wrong during the attack.");
        console.log(error);
    }
}

// Called when the user clicks the switch button in battle, this function sends the user's choice for which lucid to switch into battle to the backend,
async function switchLucid(ownedLucidId) {
    try {
        // Uses a POST request to send the user's choice for which lucid to switch into battle to the backend, 
        const response = await fetch("/game/battle/switch/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie()
            },
            body: JSON.stringify({
                owned_lucid_id: ownedLucidId
            })
        });

        const data = await response.json();

        if (!response.ok) {
            showGameMessage(data.error || "Could not switch Lucid.");
            return;
        }

        handleBattleResult(data);
    } catch (error) {
        showGameMessage("Something went wrong while switching.");
        console.log(error);
    }
}

// Called when the user clicks the "Run" button in battle, 
async function runBattle() {
    try {
        // Uses a POST request to send to the backend that the user wants to run from battle, 
        // the backend then processes that action and returns the updated battle data to be shown in the frontend 
        const response = await fetch("/game/battle/run/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie()
            }
        });

        const data = await response.json();

        if (!response.ok) {
            showGameMessage(data.error || "Could not run from battle.");
            return;
        }

        // The result of running will be used in handleBattleResult() to show the appropriate message to the user 
        // and update the battle UI accordingly
        handleBattleResult(data);
    } catch (error) {
        showGameMessage("Something went wrong while running.");
        console.log(error);
    }
}

// This is responsible for handling the result of any battle action (attacking or running) 
// and updating the UI accordingly, whether that be showing the updated battle if it's still ongoing, 
function handleBattleResult(data) {
    if (data.result === "ongoing" || data.result === "awaiting_switch") {
        showGameMessage("Battle updated.");
        showBattle(data.battle);
        return;
    }

    battleSection.innerHTML = "";

    // Depending on the result of the battle, it will show the user what happened, and what they have earned/lost
    if (data.result === "victory") {
        showGameMessage(`You won and caught ${data.caught.name}!`);
    } else if (data.result === "loss") {
        showGameMessage("You lost the battle.");
    } else if (data.result === "ran") {
        showGameMessage("You ran away from the battle.");
    }

    nextButton.style.display = "inline-block"; // Shows the "Next" button that allows user to continue to the main hub of the game after battle
}

// This function is responsible for showing the battle log to the user, 
// which gives a play by play of the battle actions that have happened so far, and is updated after every battle action
function showBattleLog(log) {
    const battleLog = document.getElementById("battle-log");

    let html = "<h4>Battle Log</h4>";

    // Loops through the battle log array and creates a paragraph for each log entry to show to the user
    for (let i = 0; i < log.length; i++) {
        html += `<p>${log[i]}</p>`;
    }

    battleLog.innerHTML = html;
}

loadStarterData();

const djangoMessages = document.querySelectorAll(".django-message");

// // Loops through any messages that were sent from the Django backend (like error messages for trying to create an alarm within 5 hours of the current time) 
// // and shows them to the user in an alert box
// for (let i = 0; i < djangoMessages.length; i++) {
//     alert(djangoMessages[i].textContent);
// }