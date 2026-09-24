SCAN_PHONE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Lloyd Bar Scanner</title>
<style>
        * { 
            box-sizing: border-box; 
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
        }
        body { 
            background-color: #0b0f19; 
            color: #eceff1; 
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            min-height: 100dvh;
            padding: 16px;
        }
        .upload-card { 
            background: #161f30; 
            border: 1px solid #1f2d47; 
            border-radius: 16px; 
            padding: 32px 20px; 
            width: 100%;
            max-width: 360px;
            text-align: center;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        }
        h2 { 
            color: #00E5FF; 
            font-size: 20px; 
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }
        p { 
            color: #90a4ae; 
            font-size: 14px; 
            line-height: 1.4;
            margin-bottom: 28px; 
        }
        input[type="file"] { 
            display: none; 
        }
        .action-btn {
            background-color: #00E5FF; 
            color: #000; 
            font-size: 15px; 
            font-weight: bold;
            padding: 16px 24px; 
            border-radius: 10px; 
            border: none; 
            cursor: pointer;
            display: block; 
            width: 100%; 
            transition: background-color 0.15s, transform 0.1s;
        }
        .action-btn:active { 
            background-color: #18ffff; 
            transform: scale(0.97); 
        }
        #status { 
            font-weight: bold; 
            margin-top: 18px; 
            font-size: 14px; 
            min-height: 20px; 
        }
    </style>
</head>
<body>
    <div class="upload-card">
        <h2>LLOYD BAR SCANNER</h2>
        <p>Snap bottles & bar tools to feed directly into the agent.</p>
        <label for="cameraInput" class="action-btn">📷 SNAP / UPLOAD</label>
        <input type="file" id="cameraInput" accept="image/*" capture="environment">
        <div id="status"></div>
    </div>

    <script>
    const input = document.getElementById('cameraInput');
    const statusDiv = document.getElementById('status');

    input.addEventListener('change', async () => {
        if (!input.files || !input.files[0]) return;
        const file = input.files[0];

        statusDiv.style.color = '#00E5FF';
        statusDiv.innerText = 'Transmitting to laptop...';

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                headers: { 'X-Filename': file.name },
                body: file
            });

            if (response.ok) {
                statusDiv.style.color = '#00E676';
                statusDiv.innerText = '✓ Delivered to Lloyd!';
                setTimeout(() => { statusDiv.innerText = ''; }, 4000);
            } else {
                throw new Error('Upload error');
            }
        } catch (err) {
            statusDiv.style.color = '#FF5252';
            statusDiv.innerText = 'Upload failed. Ensure laptop is reachable.';
        }
    });
    </script>
</body>
</html>
"""