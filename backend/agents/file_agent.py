import os
import shutil
from agents.base_agent import BaseAgent

class FileAgent(BaseAgent):
    name = "file_agent"

    FILE_TYPES = {
        "Documents": [".pdf", ".doc", ".docx", ".txt", ".ppt", ".pptx", ".xls", ".xlsx"],
        "Images": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
        "Videos": [".mp4", ".mkv", ".avi", ".mov"],
        "Audio": [".mp3", ".wav", ".aac"],
        "Archives": [".zip", ".rar", ".7z"],
        "Code": [".py", ".js", ".jsx", ".html", ".css", ".java", ".cpp"]
    }

    def get_category(self, filename):
        ext = os.path.splitext(filename)[1].lower()
        for category, exts in self.FILE_TYPES.items():
            if ext in exts:
                return category
        return "Others"

    # ---------- Existing methods ----------
    def organize_downloads(self):
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.exists(downloads_path):
            return {"success": False, "message": "Downloads folder not found."}

        moved_files = []
        for filename in os.listdir(downloads_path):
            file_path = os.path.join(downloads_path, filename)
            if not os.path.isfile(file_path):
                continue
            category = self.get_category(filename)
            category_path = os.path.join(downloads_path, category)
            os.makedirs(category_path, exist_ok=True)
            dest = os.path.join(category_path, filename)
            if os.path.exists(dest):
                name, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(dest):
                    new_name = f"{name}_{counter}{ext}"
                    dest = os.path.join(category_path, new_name)
                    counter += 1
            shutil.move(file_path, dest)
            moved_files.append({"file": filename, "category": category})

        return {
            "success": True,
            "agent": self.name,
            "action": "organize_downloads",
            "files_moved": len(moved_files),
            "details": moved_files
        }

    def scan_downloads(self):
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.exists(downloads_path):
            return {"success": False, "message": "Downloads folder not found."}
        files = [f for f in os.listdir(downloads_path) if os.path.isfile(os.path.join(downloads_path, f))]
        return {"success": True, "agent": self.name, "action": "scan_downloads", "files_found": len(files)}

    # ---------- New methods ----------
    def arrange_folder(self, folder_path: str) -> dict:
        if not os.path.exists(folder_path):
            return {"success": False, "agent": self.name, "message": f"Folder '{folder_path}' does not exist."}
        if not os.path.isdir(folder_path):
            return {"success": False, "agent": self.name, "message": f"'{folder_path}' is not a folder."}

        moved = []
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if not os.path.isfile(file_path):
                continue
            category = self.get_category(filename)
            category_path = os.path.join(folder_path, category)
            os.makedirs(category_path, exist_ok=True)
            dest = os.path.join(category_path, filename)
            if os.path.exists(dest):
                name, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(dest):
                    new_name = f"{name}_{counter}{ext}"
                    dest = os.path.join(category_path, new_name)
                    counter += 1
            shutil.move(file_path, dest)
            moved.append({"file": filename, "category": category})

        return {
            "success": True,
            "agent": self.name,
            "action": "arrange_folder",
            "folder": folder_path,
            "files_moved": len(moved),
            "details": moved
        }

    def delete_folder(self, folder_path: str) -> dict:
        if not os.path.exists(folder_path):
            return {"success": False, "agent": self.name, "message": f"Folder '{folder_path}' does not exist."}
        if not os.path.isdir(folder_path):
            return {"success": False, "agent": self.name, "message": f"'{folder_path}' is not a folder."}
        try:
            shutil.rmtree(folder_path)
            return {
                "success": True,
                "agent": self.name,
                "action": "delete_folder",
                "folder": folder_path,
                "message": f"Folder '{folder_path}' deleted successfully."
            }
        except Exception as e:
            return {"success": False, "agent": self.name, "message": f"Deletion failed: {str(e)}"}

    # ---------- execute ----------
    def execute(self, command: str) -> dict:
        command_lower = command.lower()

        if "organize" in command_lower and "download" in command_lower:
            return self.organize_downloads()

        elif "scan" in command_lower and "download" in command_lower:
            return self.scan_downloads()

        elif "arrange" in command_lower and "folder" in command_lower:
            parts = command.split("arrange folder", 1)
            if len(parts) == 2:
                folder_path = parts[1].strip()
                return self.arrange_folder(folder_path)
            else:
                return {"success": False, "agent": self.name, "message": "Please specify folder path: arrange folder <path>"}

        elif "delete" in command_lower and "folder" in command_lower:
            parts = command.split("delete folder", 1)
            if len(parts) == 2:
                folder_path = parts[1].strip()
                return self.delete_folder(folder_path)
            else:
                return {"success": False, "agent": self.name, "message": "Please specify folder path: delete folder <path>"}

        else:
            return {"success": False, "agent": self.name, "message": "File Agent: Command not understood."}