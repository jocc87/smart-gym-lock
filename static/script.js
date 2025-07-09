// ⏳ Oldal betöltésekor statisztika betöltése
document.addEventListener("DOMContentLoaded", function () {
    loadStats();
});

// 📊 STATISZTIKA LEKÉRÉSE API-BÓL
function loadStats() {
    fetch('/api/user_stats')
        .then(res => res.json())
        .then(data => {
            const tableBody = document.getElementById("stats-body");

            // Előző sorok törlése
            tableBody.innerHTML = "";

            // Új sorok hozzáadása
            data.forEach(stat => {
                const row = document.createElement("tr");

                row.innerHTML = `
                    <td>${stat.username}</td>
                    <td>${stat.nyitasok}</td>
                    <td>${stat.sikeres}</td>
                    <td>${stat.sikertelen}</td>
                `;

                tableBody.appendChild(row);
            });
        })
        .catch(err => {
            console.error("❌ Hiba a stat lekérésnél:", err);
        });
}

// ✅ TAGSÁGI JOGOK ELLENŐRZÉSE
document.getElementById("member-form").addEventListener("submit", async function (event) {
    event.preventDefault(); // Alapértelmezett elküldés tiltása

    const memberId = document.getElementById("member-id").value;
    const resultDiv = document.getElementById("result");

    // Előző eredmény törlése
    resultDiv.innerHTML = "";

    try {
        const response = await fetch(`/api/rights/${memberId}`);
        const data = await response.json();

        if (data.length === 0) {
            resultDiv.innerHTML = `<p>Nincs találat a tagsági kódhoz: ${memberId}</p>`;
        } else {
            const list = document.createElement("ul");
            data.forEach(right => {
                const listItem = document.createElement("li");
                listItem.textContent = `${right.gym_name}: ${right.start_date} - ${right.end_date}`;
                list.appendChild(listItem);
            });
            resultDiv.appendChild(list);
        }
    } catch (error) {
        console.error("❌ API hiba:", error);
        resultDiv.innerHTML = `<p>Hiba történt az adatlekérés során.</p>`;
    }
});

// 🛒 KÓDVÁSÁRLÁS VÉGREHAJTÁSA
document.getElementById("order-form").addEventListener("submit", async function (event) {
    event.preventDefault();

    const username = document.getElementById("order-username").value;
    const passcode = document.getElementById("order-passcode").value;
    const responseBox = document.getElementById("order-response");
    responseBox.innerHTML = "";

    try {
        console.log("📤 Küldésre készül:", { username, passcode });
        const res = await fetch("/api/order", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, passcode })
        });

        const result = await res.json();

        if (res.ok) {
            responseBox.innerHTML = `<p style="color:green;">✅ ${result.message} (ID: ${result.order_id})</p>`;
        } else {
            responseBox.innerHTML = `<p style="color:red;">❌ ${result.error}</p>`;
        }
    } catch (err) {
        console.error("❌ API hiba:", err);
        responseBox.innerHTML = `<p style="color:red;">Hálózati hiba történt.</p>`;
    }
});
