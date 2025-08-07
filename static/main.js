document.addEventListener("DOMContentLoaded", () => {
    // Constants for selectors
    const form = document.getElementById("caseForm");
    const submitBtn = document.getElementById("submitBtn");
    const btnText = document.getElementById("btnText");
    const loadingSpinner = document.getElementById("loadingSpinner");
    const resetBtn = document.getElementById("resetBtn");
    const errorMsg = document.getElementById("errorMsg");
    const errorText = document.getElementById("errorText");
    const offlineMsg = document.getElementById("offlineMsg");
    const skeletonLoader = document.getElementById("skeletonLoader");
    const results = document.getElementById("results");
    const caseCard = document.getElementById("caseCard");
    const ordersCard = document.getElementById("ordersCard");
    const petitioner = document.getElementById("petitioner");
    const respondent = document.getElementById("respondent");
    const filingDate = document.getElementById("filingDate");
    const nextHearing = document.getElementById("nextHearing");
    const ordersList = document.getElementById("ordersList");
    const pagination = document.getElementById("pagination");
    const prevPage = document.getElementById("prevPage");
    const nextPage = document.getElementById("nextPage");
    const darkModeToggle = document.getElementById("darkModeToggle");
    const htmlEl = document.documentElement;

    // Demo data for preview and fallback
    const DEMO_CASE = {
        petitioner: "John Doe",
        respondent: "Jane Smith",
        filing_date: "2022-01-15",
        next_hearing: "2023-06-10",
        orders: [
            { name: "Order #1", url: "#" },
            { name: "Order #2", url: "#" },
            { name: "Order #3", url: "#" }
        ]
    };

    // Helper: Enable/disable submit button based on form validity
    function validateForm() {
        const caseType = form.caseType.value;
        const caseNumber = form.caseNumber.value;
        const filingYear = form.filingYear.value;
        submitBtn.disabled = !(caseType && caseNumber && filingYear && Number(caseNumber) > 0 && Number(filingYear) >= 1900 && Number(filingYear) <= 2099);
    }

    // Helper: Show skeleton loader
    function showSkeleton() {
        skeletonLoader.classList.remove("hidden");
        results.classList.add("hidden");
        errorMsg.classList.add("hidden");
        offlineMsg.classList.add("hidden");
    }

    // Helper: Hide skeleton loader
    function hideSkeleton() {
        skeletonLoader.classList.add("hidden");
    }

    // Helper: Show error message
    function showError(msg) {
        errorText.textContent = msg;
        errorMsg.classList.remove("hidden");
        results.classList.add("hidden");
        hideSkeleton();
    }

    // Helper: Show offline message
    function showOffline() {
        offlineMsg.classList.remove("hidden");
        errorMsg.classList.add("hidden");
        results.classList.add("hidden");
        hideSkeleton();
    }

    // Helper: Animate cards in
    function animateCards() {
        caseCard.classList.remove("opacity-0", "translate-y-4");
        ordersCard.classList.remove("opacity-0", "translate-y-4");
    }

    // Helper: Render case details and orders
    function renderResults(data) {
        petitioner.textContent = data.petitioner || "Not found";
        respondent.textContent = data.respondent || "Not found";
        filingDate.textContent = data.filing_date || "Not found";
        nextHearing.textContent = data.next_hearing || "Not found";
        // Orders/judgments list
        ordersList.innerHTML = "";
        (data.orders || []).forEach((order, idx) => {
            const li = document.createElement("li");
            li.className = "flex items-center justify-between";
            li.innerHTML = `
                <span class="text-gray-700 dark:text-gray-200">${order.name}</span>
                <a href="${order.url}" target="_blank" class="ml-2 text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200 transition flex items-center gap-1" aria-label="Download PDF">
                    <i data-feather="download" class="w-5 h-5"></i>
                </a>
            `;
            ordersList.appendChild(li);
        });
        feather.replace();
        // Pagination (demo: hide if <= 5)
        if ((data.orders || []).length > 5) {
            pagination.classList.remove("hidden");
        } else {
            pagination.classList.add("hidden");
        }
        hideSkeleton();
        results.classList.remove("hidden");
        setTimeout(animateCards, 100); // Animate in
    }

    // Helper: Reset form and results
    function resetAll() {
        form.reset();
        validateForm();
        results.classList.add("hidden");
        errorMsg.classList.add("hidden");
        offlineMsg.classList.add("hidden");
        hideSkeleton();
        caseCard.classList.add("opacity-0", "translate-y-4");
        ordersCard.classList.add("opacity-0", "translate-y-4");
    }

    // Dark mode toggle logic
    function setDarkMode(enabled) {
        if (enabled) {
            htmlEl.classList.add("dark");
            localStorage.setItem("darkMode", "true");
        } else {
            htmlEl.classList.remove("dark");
            localStorage.setItem("darkMode", "false");
        }
    }
    darkModeToggle.addEventListener("click", () => {
        setDarkMode(!htmlEl.classList.contains("dark"));
    });
    if (localStorage.getItem("darkMode") === "true") setDarkMode(true);

    // Offline detection
    window.addEventListener("offline", showOffline);
    window.addEventListener("online", () => { offlineMsg.classList.add("hidden"); });

    // Form validation
    form.addEventListener("input", validateForm);

    // Form submission
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        if (!navigator.onLine) {
            showOffline();
            return;
        }
        showSkeleton();
        submitBtn.disabled = true;
        btnText.classList.add("opacity-50");
        loadingSpinner.classList.remove("hidden");
        errorMsg.classList.add("hidden");
        results.classList.add("hidden");
        caseCard.classList.add("opacity-0", "translate-y-4");
        ordersCard.classList.add("opacity-0", "translate-y-4");

        // Get form values
        const caseType = form.caseType.value;
        const caseNumber = form.caseNumber.value;
        const filingYear = form.filingYear.value;

        try {
            // Call backend API (replace with actual endpoint)
            const response = await fetch("/fetch-case", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ case_type: caseType, case_number: caseNumber, filing_year: filingYear })
            });
            const data = await response.json();

            if (!response.ok || !data || data.error) {
                throw new Error(data.error || "No data found for this case.");
            }

            // If backend returns PDF links as a single url, wrap in array for UI
            if (!Array.isArray(data.orders) && data.pdf_url) {
                data.orders = [{ name: "Latest Order", url: data.pdf_url }];
            }
            renderResults(data);
        } catch (err) {
            showError(err.message);
        } finally {
            submitBtn.disabled = false;
            btnText.classList.remove("opacity-50");
            loadingSpinner.classList.add("hidden");
        }
    });

    // Reset button
    resetBtn.addEventListener("click", resetAll);

    // Pagination demo (no backend yet)
    prevPage.addEventListener("click", () => {});
    nextPage.addEventListener("click", () => {});

    // Show demo data on load for preview
    window.addEventListener("DOMContentLoaded", () => {
        renderResults(DEMO_CASE);
        validateForm();
    });
});
