# ============================================================
#  train_classifier.py — Train the ML Document Classifier
#
#  Run this ONCE before starting the app:
#    python train_classifier.py
#
#  What it does:
#    - Takes labelled training examples (text + document type)
#    - Trains a TF-IDF + Logistic Regression classifier
#    - Saves the model to app/models/classifier_model.pkl
#
#  After training, the app uses this model to automatically
#  identify whether a document is an invoice, receipt, or
#  bank statement.
# ============================================================

import sys
import os

# Make sure Python can find our app modules
sys.path.insert(0, os.path.dirname(__file__))

from app.services.classifier import train_and_save_model

# ── Training Data ─────────────────────────────────────────────────────────────
# Format: ("sample text from document", "label")
# The more examples you add, the better the model gets!

TRAINING_DATA = [

    # ── INVOICE examples ──────────────────────────────────────────────────────
    # Real invoices have: invoice number, bill to, GST, due date, vendor
    ("Invoice No: INV-001 Bill To: ABC Pvt Ltd Due Date: 12/03/2024 GST 500 Amount 5000 Vendor XYZ Corp", "invoice"),
    ("Tax Invoice GSTIN 27AABCU9603R1ZX Invoice Number 2024/001 Net Payable 12000 Ship To Customer XYZ", "invoice"),
    ("Purchase Order Invoice Date 01/01/2024 Subtotal 8000 Tax 720 Grand Total 8720 Supplier Tech Corp", "invoice"),
    ("Proforma Invoice Client Name ABC Ltd Due Date 30 days Payment Terms Net 30 Amount Due 2500", "invoice"),
    ("Invoice for professional consulting services rendered Amount Due 15000 INR Vendor Solutions Pvt", "invoice"),
    ("Commercial Invoice Export Bill of Lading Total Value Buyer ABC Company Invoice No EXP-2024-001", "invoice"),
    ("Service Invoice Client ABC Ltd Invoice Date March 2024 Professional Fees 25000 GST 4500", "invoice"),
    ("Retail Invoice Customer Copy Bill To Address GST Number Items Purchased Total Payable Amount", "invoice"),
    ("Invoice No 456 Billed To Raj Enterprises Due Date 15/04/2024 Amount ₹8500 Tax ₹1530", "invoice"),
    ("Monthly Invoice Subscription Services Invoice Date 01/03/2024 Amount Due 999 USD Vendor SaaS Co", "invoice"),

    # ── RECEIPT examples ──────────────────────────────────────────────────────
    # Real receipts have: receipt number, total paid, cashier, store name
    ("Receipt No 456 Thank you for your purchase Total Paid 320 Cashier John Store Big Mart Date", "receipt"),
    ("Sales Receipt Items Bread 30 Milk 40 Eggs 50 Subtotal 120 Tax 10 Total 130 Cash Payment Change 20", "receipt"),
    ("Payment Receipt Received from customer Amount 1500 Mode UPI Transaction ID TXN123456 Balance NIL", "receipt"),
    ("Shop Receipt Counter 3 Cashier Mary Subtotal 450 GST 45 Total 495 Paid by Card No Change", "receipt"),
    ("Restaurant Receipt Table 4 Order Burger Fries Coke Total 650 Service Charge 65 Card Payment", "receipt"),
    ("Petrol Pump Receipt Fuel Diesel Litres 20 Rate 92 Amount 1840 Vehicle No MH12AB1234", "receipt"),
    ("Medical Receipt Patient Name Consultation Fee Medicines Total Bill 3500 Paid by Card", "receipt"),
    ("Grocery Store Receipt Vegetables Fruits Dairy Total Paid Cash Thank You Please Visit Again", "receipt"),
    ("Receipt Thank you shopping with us Total Amount Paid Debit Card Last 4 Digits 4321", "receipt"),
    ("POS Receipt Outlet Mall Store Item Discount Loyalty Points Earned Total Due Paid", "receipt"),

    # ── BANK STATEMENT examples ───────────────────────────────────────────────
    # Real bank statements have: account number, balance, debit/credit entries
    ("Bank Statement Account Number 123456789 Opening Balance 50000 Closing Balance 45000 HDFC Bank", "bank_statement"),
    ("Monthly Statement January 2024 Debit 5000 Credit 2000 NEFT Transfer UPI Payment Balance", "bank_statement"),
    ("Account Statement Period Jan 2024 Withdrawals Deposits Net Balance 47000 Branch Mumbai", "bank_statement"),
    ("HDFC Bank Account Summary IFSC HDFC0001234 IMPS NEFT Transactions Customer ID 789", "bank_statement"),
    ("SBI Bank Statement Passbook Customer ID Balance 25000 Transaction History Debit Credit Entry", "bank_statement"),
    ("Account No 9876543210 Statement Date 31 Mar 2024 Closing Balance 123456 ICICI Bank Branch", "bank_statement"),
    ("Credit Card Statement Outstanding Amount Minimum Due Payment Due Date Transactions Charges", "bank_statement"),
    ("Savings Account Statement Nominee Branch IFSC Code Opening Closing Balance Passbook Update", "bank_statement"),
    ("Bank Passbook Account Holder Name Branch Name Transaction Date Particulars Debit Credit Balance", "bank_statement"),
    ("Current Account Statement Business Account Cheque Clearance RTGS NEFT Corporate Banking", "bank_statement"),
]


# ── Run Training ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("  DocExtractor — Training Document Classifier")
    print("=" * 55)

    # Separate text and labels
    texts  = [sample[0] for sample in TRAINING_DATA]
    labels = [sample[1] for sample in TRAINING_DATA]

    # Show class distribution
    print(f"\nTraining samples:")
    for label in ["invoice", "receipt", "bank_statement"]:
        count = labels.count(label)
        print(f"  {label:20s}: {count} samples")

    print(f"\nTotal: {len(texts)} samples\n")

    # Train and save
    model_path = "app/models/classifier_model.pkl"
    train_and_save_model(texts, labels, save_path=model_path)

    print("\n✅ Training complete!")
    print(f"   Model saved to: {model_path}")
    print("\nYou can now run: python run.py")
    print("=" * 55)
