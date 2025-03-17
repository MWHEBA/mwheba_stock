import subprocess

# Define the Git commands
commands = [
    "git add .",
    'git commit -m "Resolved merge conflicts"',
    "git push origin main"
]

def run_git_commands():
    for command in commands:
        try:
            print(f"\n🚀 Running: {command}")
            result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"❌ Error: {e.stderr}")
            break

if __name__ == "__main__":
    run_git_commands()
