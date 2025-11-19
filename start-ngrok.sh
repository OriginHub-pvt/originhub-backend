#!/bin/bash

# Start ngrok tunnel for webhook endpoint
echo "🚀 Starting ngrok tunnel..."
echo ""
echo "Your webhook URL will be: https://YOUR-NGROK-URL.ngrok-free.app/webhooks/clerk"
echo ""
echo "⚠️  Note: Update the URL in Clerk dashboard after ngrok starts"
echo ""
echo "Press Ctrl+C to stop ngrok"
echo ""

ngrok http 8000

