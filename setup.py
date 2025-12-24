# Instagram AI DM Auto-Responder Pro | @samiXmoiz_bot
# Setup Wizard - Guides users through configuration

import os
import sys
import shutil
import time
import subprocess

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    print("\n")
    print("╔" + "═" * 54 + "╗")
    print("║" + " " * 54 + "║")
    print("║   🤖 Instagram AI DM Auto-Responder Pro            ║")
    print("║   Setup Wizard                                      ║")
    print("║" + " " * 54 + "║")
    print("║   📦 @samiXmoiz_bot                                 ║")
    print("║" + " " * 54 + "║")
    print("╚" + "═" * 54 + "╝")
    print("\n")

def print_step(current, total, message):
    print(f"\n  [Step {current}/{total}] {message}")
    print("  " + "-" * 50)

def get_input(prompt, hidden=False):
    if hidden:
        import getpass
        return getpass.getpass(f"  → {prompt}: ")
    else:
        return input(f"  → {prompt}: ")

def show_menu(title, options):
    print(f"\n  {title}")
    for i, option in enumerate(options, 1):
        print(f"    {i}. {option}")
    print()
    while True:
        try:
            choice = int(input("  → Enter your choice (number): "))
            if 1 <= choice <= len(options):
                return choice
            print("  ⚠️  Invalid choice, try again.")
        except ValueError:
            print("  ⚠️  Please enter a number.")

def install_dependencies():
    print("\n  📦 Installing dependencies...")
    print("  " + "-" * 50)
    try:
        subprocess.run([sys.executable, "install.py"], check=True)
        print("\n  ✅ Dependencies installed successfully!")
        return True
    except Exception as e:
        print(f"\n  ❌ Error installing dependencies: {e}")
        return False

def save_config(username, password, language, use_proxy, group_messages):
    env_content = f"""IG_USERNAME={username}
IG_PASSWORD={password}
LANGUAGE={language}
USE_PROXY={'true' if use_proxy else 'false'}
GROUP_MESSAGES={'true' if group_messages else 'false'}
"""
    with open('.env', 'w') as f:
        f.write(env_content)
    print("\n  ✅ Configuration saved to .env")

def copy_template(template_name):
    templates = {
        1: 'templates/knowledge_business.txt',
        2: 'templates/knowledge_dating.txt',
        3: 'templates/knowledge_shilling.txt'
    }
    
    template_path = templates.get(template_name)
    if template_path and os.path.exists(template_path):
        shutil.copy(template_path, 'knowledge.txt')
        print(f"\n  ✅ Template copied to knowledge.txt")
        print("  💡 You can customize knowledge.txt later with your details!")
        return True
    else:
        # Create a basic knowledge file
        with open('knowledge.txt', 'w') as f:
            f.write("# Add your business info, personality, or promo details here\n")
        print("\n  ⚠️  Template not found. Created blank knowledge.txt")
        return False

def run_bot():
    print("\n  🚀 Starting the bot...")
    print("  " + "-" * 50)
    print("  Press Ctrl+C to stop the bot at any time.\n")
    time.sleep(2)
    subprocess.run([sys.executable, "main.py"])

def main():
    clear_screen()
    print_banner()
    
    print("  Welcome! This wizard will help you set up your Instagram DM bot.")
    print("  Just follow the steps below.\n")
    input("  Press ENTER to continue...")
    
    # Step 1: Install dependencies
    clear_screen()
    print_banner()
    print_step(1, 5, "Installing Dependencies")
    
    install_choice = input("  Do you want to install/update dependencies? (y/n): ").lower()
    if install_choice == 'y':
        if not install_dependencies():
            print("\n  ⚠️  There was an issue. You may need to install manually.")
            input("  Press ENTER to continue anyway...")
    
    # Step 2: Instagram credentials
    clear_screen()
    print_banner()
    print_step(2, 5, "Instagram Credentials")
    print("  Enter your Instagram login details.\n")
    
    username = get_input("Instagram username or email")
    password = get_input("Instagram password", hidden=True)
    
    # Step 3: Choose language
    clear_screen()
    print_banner()
    print_step(3, 5, "Response Language")
    
    languages = ["English", "Spanish", "French", "German", "Portuguese", "Turkish", "Other"]
    lang_choice = show_menu("What language should the bot respond in?", languages)
    
    if lang_choice == 7:
        language = get_input("Enter your language")
    else:
        language = languages[lang_choice - 1].lower()
    
    # Step 4: Choose use case / template
    clear_screen()
    print_banner()
    print_step(4, 5, "Choose Your Use Case")
    
    use_cases = [
        "💼 Business & Customer Support",
        "💕 Dating & Social",
        "📢 Marketing & Promotion",
        "📝 Custom (blank template)"
    ]
    template_choice = show_menu("What will you use this bot for?", use_cases)
    
    # Step 5: Additional options
    clear_screen()
    print_banner()
    print_step(5, 5, "Additional Options")
    
    proxy_choice = input("  Do you want to use proxies? (y/n): ").lower()
    use_proxy = proxy_choice == 'y'
    
    if use_proxy:
        print("\n  ℹ️  Add your proxies to proxies.txt (one per line)")
        print("     Format: username:password@host:port")
    
    group_choice = input("\n  Respond to group messages? (y/n): ").lower()
    group_messages = group_choice == 'y'
    
    # Save everything
    clear_screen()
    print_banner()
    print("\n  ⏳ Setting up your bot...")
    print("  " + "-" * 50)
    
    save_config(username, password, language, use_proxy, group_messages)
    copy_template(template_choice)
    
    # Final summary
    clear_screen()
    print_banner()
    print("  ✅ SETUP COMPLETE!")
    print("  " + "=" * 50)
    print(f"\n  📧 Account: {username}")
    print(f"  🌐 Language: {language}")
    print(f"  🔄 Proxies: {'Enabled' if use_proxy else 'Disabled'}")
    print(f"  👥 Group Messages: {'Enabled' if group_messages else 'Disabled'}")
    print(f"\n  📁 Files created:")
    print(f"     • .env (your credentials)")
    print(f"     • knowledge.txt (AI training)")
    print()
    print("  " + "=" * 50)
    
    # Start bot?
    start_choice = input("\n  🚀 Start the bot now? (y/n): ").lower()
    if start_choice == 'y':
        run_bot()
    else:
        print("\n  To start the bot later, run: python main.py")
        print("\n  Thank you for using @samiXmoiz_bot! 🎉\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  👋 Setup cancelled. Goodbye!\n")
        sys.exit(0)
