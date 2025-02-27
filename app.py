from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import matplotlib.pyplot as plt
import io
import base64
import google.generativeai as genai

app = Flask(__name__)

# Initialize variables
income = 0.0
expenses = []
savings = 0.0

# Load transactions data from file
def load_data():
    global income, expenses, savings
    try:
        with open('transactions.json', 'r') as file:
            data = json.load(file)
            income = data.get('income', 0.0)
            expenses = data.get('expenses', [])
            savings = data.get('savings', 0.0)
    except FileNotFoundError:
        pass

# Save transactions data to file
def save_data():
    data = {
        'income': income,
        'expenses': expenses,
        'savings': savings
    }
    with open('transactions.json', 'w') as file:
        json.dump(data, file)

# Clear all data
def clear_data():
    global income, expenses, savings
    income = 0.0
    expenses = []
    savings = 0.0
    save_data()

# Calculate savings
def calculate_savings():
    global income, expenses, savings
    total_expenses = sum(expense['amount'] for expense in expenses)
    savings = income - total_expenses
    save_data()

# Gemini AI API integration for financial tips
def get_financial_tips(income, savings, expenses):
    API_KEY = "AIzaSyDTPHL6MHjQQ1o3zuKwBLpen1VzD7e0XGA"  # Replace with your actual API key
    genai.configure(api_key=API_KEY)

    # Get expense categories and amounts
    categories = {}
    for expense in expenses:
        category = expense['category']
        amount = expense['amount']
        categories[category] = categories.get(category, 0) + amount

    total_expenses = sum(expense['amount'] for expense in expenses)

    # Create a prompt for Gemini
    prompt = f"""
    Based on the following financial information, provide 3-5 personalized financial tips:

    Income: ${income:.2f}
    Total Expenses: ${total_expenses:.2f}
    Current Savings: ${savings:.2f}

    Expense breakdown by category:
    {', '.join([f"{category}: ${amount:.2f}" for category, amount in categories.items()])}

    Please focus on practical advice for budgeting, saving money, and financial planning.
    """

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")  # Use the latest correct model
        response = model.generate_content(prompt)
        
        if response and hasattr(response, "text"):
            tips = response.text.split("\n")
            return [tip.strip("-•* ") for tip in tips if tip.strip()]
        return ["No tips available."]
    except Exception as e:
        print(f"Error generating financial tips: {e}")
        return [f"Error: {str(e)}"]

# Home route
@app.route('/')
def home():
    load_data()
    return render_template('index.html', income=income, expenses=expenses, savings=savings)

# Add income
@app.route('/add_income', methods=['POST'])
def add_income():
    global income
    amount = float(request.form['amount'])
    income = amount  # Replace income instead of adding
    calculate_savings()
    save_data()
    return jsonify({'success': True, 'message': 'Income updated successfully!'})

# Add expense
@app.route('/add_expense', methods=['POST'])
def add_expense():
    global expenses
    description = request.form['description']
    amount = float(request.form['amount'])
    category = request.form['category']
    expenses.append({'description': description, 'amount': amount, 'category': category})
    calculate_savings()
    save_data()
    return jsonify({'success': True, 'message': 'Expense added successfully!'})

# Edit expense
@app.route('/edit_expense/<int:index>', methods=['POST'])
def edit_expense(index):
    if 0 <= index < len(expenses):
        expenses[index]['description'] = request.form['description']
        expenses[index]['amount'] = float(request.form['amount'])
        expenses[index]['category'] = request.form['category']
        calculate_savings()
        save_data()
    return jsonify({'success': True, 'message': 'Expense updated successfully!'})

# Delete expense
@app.route('/delete_expense/<int:index>', methods=['POST'])
def delete_expense(index):
    if 0 <= index < len(expenses):
        expenses.pop(index)
        calculate_savings()
        save_data()
    return jsonify({'success': True, 'message': 'Expense deleted successfully!'})

# Fetch financial tips
@app.route('/fetch_tips', methods=['POST'])
def fetch_tips():
    financial_tips = get_financial_tips(income, savings, expenses)
    return jsonify({'tips': financial_tips})

# Generate expense chart
@app.route('/expense_chart')
def expense_chart():
    try:
        categories = {expense['category'] for expense in expenses}
        category_expenses = {category: 0.0 for category in categories}
        
        for expense in expenses:
            category_expenses[expense['category']] += expense['amount']

        labels, values = list(category_expenses.keys()), list(category_expenses.values())

        plt.figure(figsize=(8, 6))
        plt.pie(values, labels=labels, autopct='%1.1f%%')
        plt.title('Expenses by Category')
        plt.axis('equal')

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plot_url = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close()

        return jsonify({'success': True, 'plot_url': plot_url})
    except Exception as e:
        print(f"Error generating chart: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Clear all financial data
@app.route('/clear_data', methods=['POST'])
def clear_financial_data():
    clear_data()
    return jsonify({'success': True, 'message': 'All financial data cleared successfully!'})

# Run the app
if __name__ == '__main__':
    app.run(debug=True)