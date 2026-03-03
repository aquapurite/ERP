/**
 * CJDQuick OMS Webhook Receiver
 *
 * URL: https://www.aquapurite.org/api/webhooks/cjdquick
 *
 * Receives real-time status updates from CJDQuick OMS:
 *   - order.confirmed, order.shipped, order.cancelled
 *   - shipment.tracking_updated, shipment.delivered
 *   - return.received, return.processed
 *   - ndr.raised, ndr.resolved
 *   - invoice.created, webhook.test
 *
 * Verifies HMAC-SHA256 signature, then forwards to FastAPI backend
 * which has database access to update order/shipment/return records.
 */

import crypto from "crypto";
import { NextRequest, NextResponse } from "next/server";

const WEBHOOK_SECRET = process.env.CJDQUICK_WEBHOOK_SECRET || "";
const BACKEND_URL =
  process.env.NEXT_PUBLIC_API_URL || "https://aquapurite-erp-api.onrender.com";

function verifySignature(body: string, signature: string | null): boolean {
  if (!WEBHOOK_SECRET) {
    // No secret configured — skip verification (log warning)
    console.warn("CJDQUICK_WEBHOOK_SECRET not set — skipping signature check");
    return true;
  }

  if (!signature) return false;

  const computed = crypto
    .createHmac("sha256", WEBHOOK_SECRET)
    .update(body)
    .digest("hex");

  // Handle both formats: "sha256=<hex>" and raw hex
  const expected = signature.startsWith("sha256=")
    ? `sha256=${computed}`
    : computed;

  const actual = signature.startsWith("sha256=") ? signature : signature;

  try {
    return crypto.timingSafeEqual(
      Buffer.from(expected),
      Buffer.from(actual)
    );
  } catch {
    return false;
  }
}

export async function POST(req: NextRequest) {
  const body = await req.text();
  const signature = req.headers.get("X-Webhook-Signature");
  const eventType = req.headers.get("X-OMS-Event");

  // 1. Verify signature
  if (!verifySignature(body, signature)) {
    console.error("CJDQuick webhook signature verification failed");
    return NextResponse.json({ error: "Invalid signature" }, { status: 401 });
  }

  // 2. Log receipt
  console.log(`CJDQuick webhook received: ${eventType || "unknown"}`, {
    timestamp: new Date().toISOString(),
  });

  // 3. Forward to FastAPI backend (which has DB access to update orders)
  try {
    const backendUrl = `${BACKEND_URL}/api/v1/cjdquick/webhook`;
    const forwardHeaders: Record<string, string> = {
      "Content-Type": "application/json",
    };
    // Forward signature and event headers
    if (signature) forwardHeaders["X-Webhook-Signature"] = signature;
    if (eventType) forwardHeaders["X-OMS-Event"] = eventType;

    const backendResponse = await fetch(backendUrl, {
      method: "POST",
      headers: forwardHeaders,
      body,
    });

    if (!backendResponse.ok) {
      const errorText = await backendResponse.text();
      console.error(
        `Backend webhook handler returned ${backendResponse.status}: ${errorText}`
      );
      // Still return 200 to CJDQuick to prevent retries
      // (backend failure is logged, can be retried internally)
    }

    return NextResponse.json({ received: true }, { status: 200 });
  } catch (error) {
    console.error("Error forwarding webhook to backend:", error);
    // Return 200 to prevent CJDQuick from retrying
    // Log the error for manual investigation
    return NextResponse.json(
      { received: true, warning: "Backend forwarding failed" },
      { status: 200 }
    );
  }
}
