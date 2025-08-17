const parsedList = JSON.parse(result.content);
let blockData = '';

parsedList.forEach(item => {
    let logsTable = '';

    if (Array.isArray(item.logs) && item.logs.length > 0) {
        const columns = Object.keys(item.logs[0]);

        logsTable += '<table class="logs-table" border="1"><thead><tr>';
        columns.forEach(col => {
            logsTable += `<th>${col}</th>`;
        });
        logsTable += '</tr></thead><tbody>';

        item.logs.forEach(row => {
            logsTable += '<tr>';
            columns.forEach(col => {
                logsTable += `<td>${row[col] ?? ''}</td>`;
            });
            logsTable += '</tr>';
        });

        logsTable += '</tbody></table>';
    } else {
        logsTable = '<div>No logs available</div>';
    }

    blockData = `
        <div class="result-content"> SPL Query: ${item.query}</div>
        <div class="result-content">${logsTable}</div>
        <div class="result-content">${item.summary}</div>
    `;
});

resultHTML += `
    <div class="result-item">
        <div class="result-content">${blockData}</div>
    </div>
`;
