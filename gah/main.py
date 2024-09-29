from config import load_config

def main():
    config, secrets = load_config()
    print(f"user {config.neo4j.username}")
    print(f"uri  {config.neo4j.uri}")
    print(f"pass {secrets.neo4j_password}")

if __name__ == "__main__":
    main()
