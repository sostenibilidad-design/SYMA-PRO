document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("syma-search-input");
    const suggList = document.getElementById("syma-search-sugg");

    if (!input || !suggList) return;

    let allRows = [];
    let headers = [];

    // 🔎 Detecta automáticamente la primera tabla visible
    function detectTable() {
        const tables = document.querySelectorAll("table");
        for (let tbl of tables) {
            const style = window.getComputedStyle(tbl);
            if (style.display !== "none" && tbl.offsetParent !== null) {
                return tbl;
            }
        }
        return null;
    }

    function loadTableData() {
        const table = detectTable();
        if (!table) return;

        const tbody = table.querySelector("tbody");
        allRows = Array.from(tbody.querySelectorAll("tr"));
        headers = Array.from(table.querySelectorAll("thead th")).map(th => th.textContent.trim());
    }

    // 🧹 Restaurar todas las filas
    function restoreRows() {
        allRows.forEach(row => (row.style.display = ""));
    }

    // 🔍 Filtrar según el texto
    function filterRows(query) {
        if (!query.trim()) {
            restoreRows();
            suggList.innerHTML = "";
            suggList.setAttribute("aria-hidden", "true");
            return;
        }

        const q = query.toLowerCase();
        const matches = [];

        allRows.forEach(row => {
            const text = row.innerText.toLowerCase();
            const match = text.includes(q);
            row.style.display = match ? "" : "none";
            if (match) matches.push(row);
        });

        // 🧠 Generar sugerencias (máximo 10)
        suggList.innerHTML = "";
        if (matches.length > 0) {
            matches.slice(0, 10).forEach(row => {
                const firstCell = row.querySelector("td, th");
                if (firstCell) {
                    const li = document.createElement("li");
                    li.textContent = firstCell.innerText.trim();
                    li.classList.add("syma-search__suggestion");
                    li.addEventListener("click", () => {
                        input.value = li.textContent;
                        showExact(li.textContent);
                        suggList.innerHTML = "";
                        suggList.setAttribute("aria-hidden", "true");
                    });
                    suggList.appendChild(li);
                }
            });
            suggList.setAttribute("aria-hidden", "false");
        } else {
            suggList.setAttribute("aria-hidden", "true");
        }
    }

    // 🎯 Mostrar coincidencia exacta
    function showExact(value) {
        const v = value.toLowerCase();
        allRows.forEach(row => {
            const text = row.innerText.toLowerCase();
            row.style.display = text.includes(v) ? "" : "none";
        });
    }

    // 🧭 Detectar tabla al inicio
    loadTableData();

    // 🪄 Eventos
    input.addEventListener("input", e => {
        loadTableData(); // Si cambia de subárea, vuelve a detectar
        filterRows(e.target.value);
    });

    input.addEventListener("focus", () => {
        if (input.value.trim()) suggList.setAttribute("aria-hidden", "false");
    });

    document.addEventListener("click", e => {
        if (!e.target.closest(".syma-search")) {
            suggList.innerHTML = "";
            suggList.setAttribute("aria-hidden", "true");
        }
    });
});