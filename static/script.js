let currentScanId = null;

document.getElementById('scanForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const outputDiv = document.getElementById('output');
    const downloadBtn = document.getElementById('downloadBtn');

    outputDiv.innerHTML = 'Starting scan...';
    downloadBtn.style.display = 'none';

    try {
        const response = await fetch('/scan', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok) {
            currentScanId = result.scan_id;
            outputDiv.innerHTML = `Scan started with ID: ${currentScanId}`;
            pollResults();
        } else {
            outputDiv.innerHTML = `Error: ${result.error || JSON.stringify(result)}`;
        }
    } catch (error) {
        outputDiv.innerHTML = `Error: ${error.message}`;
    }
});

async function pollResults() {
    const outputDiv = document.getElementById('output');
    const downloadBtn = document.getElementById('downloadBtn');

    while (true) {
        try {
            const response = await fetch(`/results/${currentScanId}`);
            const result = await response.json();

            if (response.ok) {
                const progress = (result.completed / result.total) * 100;
                outputDiv.innerHTML = `
                    Scan progress: ${progress.toFixed(2)}%<br>
                    Completed: ${result.completed} / ${result.total}<br>
                    Latest results:<br>
                    ${result.results.map(r => `${r.domain} (${r.protocol}): ${r.found_terms.join(', ')}`).join('<br>')}
                `;

                if (result.is_complete) {
                    outputDiv.innerHTML += '<br>Scan completed!';
                    downloadBtn.style.display = 'block';
                    break;
                }
            } else {
                outputDiv.innerHTML = `Error fetching results: ${JSON.stringify(result)}`;
                break;
            }
        } catch (error) {
            outputDiv.innerHTML = `Error: ${error.message}`;
            break;
        }

        await new Promise(resolve => setTimeout(resolve, 2000)); // Poll every 2 seconds
    }
}

document.getElementById('downloadBtn').addEventListener('click', async () => {
    if (currentScanId) {
        window.location.href = `/download/${currentScanId}`;
    }
});
