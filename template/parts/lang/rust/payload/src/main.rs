// Generated placeholder — delete when you add real code
use anyhow::Result;

fn main() -> Result<()> {
    tracing_subscriber::fmt::init();
    tracing::info!("Hello, {{project_name}}!");
    Ok(())
}

#[cfg(test)]
mod tests {
    #[test]
    fn placeholder() {}
}
