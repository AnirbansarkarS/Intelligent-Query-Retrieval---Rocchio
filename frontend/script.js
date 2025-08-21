document.getElementById('sendRequest').addEventListener('click', async () => {
    const url = "http://localhost:8000/hackrx/run"; // HTTP, not HTTPS
    const token = "c8ec8a425c4ef55d25ac5b876e2364e2b36b028c41343342ec08872bbcbf015b";

    const docUrl = document.getElementById('docUrl').value.trim();
    const questionsText = document.getElementById('questions').value.trim();

    if (!docUrl || !questionsText) {
        alert("Please enter both document URL and questions.");
        return;
    }

    const questions = questionsText.split("\n").map(q => q.trim()).filter(q => q);

    const payload = { documents: docUrl, questions: questions };

    const outputDiv = document.getElementById('responseOutput');
    outputDiv.innerHTML = "Loading...";

    try {
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": "Bearer " + token
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        outputDiv.innerHTML = "";

        if (!data.answers || !Array.isArray(data.answers)) {
            outputDiv.textContent = "Invalid response format";
            return;
        }

        // Display questions with corresponding answers
        questions.forEach((q, index) => {
            const ans = data.answers[index] || "No answer";
            const qaDiv = document.createElement('div');
            qaDiv.className = 'qa';
            qaDiv.innerHTML = `<div class="question">Q: ${q}</div><div class="answer">A: ${ans}</div>`;
            outputDiv.appendChild(qaDiv);
        });

    } catch (error) {
        outputDiv.textContent = "Error: " + error;
    }
});
