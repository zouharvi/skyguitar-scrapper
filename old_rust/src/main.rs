use std::{fs, path::PathBuf};

#[tokio::main]
async fn main() {
    fs::create_dir_all("videos").unwrap();

    let url = "https://www.youtube.com/watch?v=sBUsiVBxzEQ";
    let download_path = rustube::download_best_quality(&url).await.unwrap();

    let mut new_path = PathBuf::new();
    new_path.push("videos/");
    new_path.push(download_path.file_name().unwrap());
    fs::rename(download_path, &new_path).unwrap();
    println!("downloaded video to {:?}", new_path.as_path());
}
