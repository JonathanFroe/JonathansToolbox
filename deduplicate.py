import requests
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from PIL import Image, ImageTk
import io
from datetime import datetime
import re

#TODO Exclude RAW filetypes (raw is always prefered because it has a bigger size)

print("Input Cookie immichaccesstoken")
dryrun = False
withInterventionUI = False
immichaccesstoken = input("immichaccesstoken=")

url = "https://photos.froehlich.plus/api/duplicates"
payload = {}
headers = {
  'Accept': 'application/json'
, 'Cookie': f'immich_access_token={immichaccesstoken}; immich_auth_type=password; immich_is_authenticated=true;'
}

def create_image_frame(parent, imagedata, headers):
    """Create a frame containing image, info, and buttons"""
    frame = tk.Frame(parent, relief=tk.RAISED, borderwidth=2, padx=10, pady=10)
    
    # Download and display thumbnail
    img = download_thumbnail(imagedata.id, headers)
    if img:
        # Resize image to consistent size
        img.thumbnail((200, 200), Image.Resampling.LANCZOS)
        tk_img = ImageTk.PhotoImage(img)
        
        # Image label
        img_label = tk.Label(frame, image=tk_img)
        img_label.image = tk_img  # Keep reference
        img_label.pack(pady=5)
    
    # Info text
    info_text = f"File: {imagedata['name']}\n"
    info_text += f"CreatedDate: {imagedata['date']}\n"
    info_text += f"CreatedTime: {imagedata['time']}\n"
    size_mb = float(imagedata['filesize'])
    info_text += f"Size: {size_mb:.2f} MB\n"
    info_text += f"Megapixel: {imagedata['megapixel']}\n"
    info_text += f"Make: {imagedata['make']}\n"
    info_text += f"Namepenalty: {imagedata['namepenalty']}\n\n"
    info_text += imagedata['id']
    
    info_label = tk.Label(frame, text=info_text, justify=tk.CENTER, font=("Arial", 12))
    info_label.pack(pady=5)
    
    return frame

def imagename_penaltyscore(name):
    score = 0
    if ("WA" in name): score -= 100 # I hate Whatsapp Images
    # Remove file extension before matching
    # Remove file extension (with or without dot) before matching
    name_wo_ext = re.sub(r'[-\.]?[^-.]+$', '', name)
    match = re.search(r'-(\d+)$', name_wo_ext)
    if match:
        score -= 1
    if name and name[0].isalpha():
        score += 1
    return score

def download_thumbnail(asset_id, headers):
    """Download thumbnail for a given asset ID"""
    try:
        thumbnail_url = f"https://photos.froehlich.plus/api/assets/{asset_id}/thumbnail"
        response = requests.get(thumbnail_url, headers=headers)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content))
        else:
            print(f"Failed to download thumbnail for {asset_id}: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error downloading thumbnail for {asset_id}: {e}")
        return None

def delete_duplicates(dups):
    deleteurl = "https://photos.froehlich.plus/api/assets"
    delheaders = {
        'Content-Type': 'application/json',
        'Cookie': f'immich_access_token={immichaccesstoken}; immich_auth_type=password; immich_is_authenticated=true;'
    }
    body = {'ids': dups}
    print(f"Deleting duplicate assets: {dups}")
    if not dryrun:
        response = requests.delete(deleteurl, headers=delheaders, json=body)
        print(f"Delete status: {response.ok}, Response: {response.text}")
    if(withInterventionUI):
        window.destroy()

response = requests.request("GET", url, headers=headers, data=payload)
data = response.json()
print("Is response ok: " , response.ok)
df = pd.DataFrame(data)

for index, row in df.iterrows():
    if (withInterventionUI):
        window = tk.Tk()
        window.title(f"Duplicate Set {index + 1}")
        window.geometry("1200x600")  # Set initial window size
        
        # Create main frame
        main_frame = tk.Frame(window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add title
        title_label = tk.Label(main_frame, text=f"Duplicate Images - Set {index + 1}", 
                            font=("Arial", 14, "bold"))
        title_label.pack(pady=10)
        
        # Create a frame for the scrollable content
        canvas = tk.Canvas(main_frame)
        scrollbar = tk.Scrollbar(main_frame, orient="horizontal", command=canvas.xview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(xscrollcommand=scrollbar.set)
        
        # Pack the canvas and scrollbar
        canvas.pack(side="top", fill="both", expand=True)
        scrollbar.pack(side="bottom", fill="x")
    
    dups = pd.DataFrame(row.iloc[1])
    
    # Create a frame for each duplicate image
    dupimageinfos = []
    for index2, row2 in dups.iterrows():
        date_str = row2.localDateTime.split('T')[0]
        time_str = row2.localDateTime.split('T')[1]
        if (row2.hasMetadata):
            exif = row2.exifInfo if hasattr(row2, 'exifInfo') else {}
            file_megapixel = exif.get('exifImageWidth', 0) * exif.get('exifImageHeight', 0) / 1000000
            file_size = exif.get('fileSizeInByte', 0) / (1024 * 1024)
            make = exif.get('make', None)
            # Remove milliseconds from the date string if present
            imginfo = {'id': row2.get('id'), 'name': row2.originalFileName,  'date': date_str, 'time': time_str, 'namepenalty': imagename_penaltyscore(row2.originalFileName), 'megapixel': file_megapixel, 'filesize': file_size, 'make': make}
        else:
            imginfo = {'id': row2.get('id'), 'name': row2.originalFileName, 'date': date_str, 'time': time_str, 'namepenalty': imagename_penaltyscore(row2.originalFileName), 'megapixel': 0, 'filesize': 0, 'make': None}
        dupimageinfos.append(imginfo)
    bestimgdf = pd.DataFrame(dupimageinfos)
    imagestodelete = []
    for indexsortedimg, sortedimg, in bestimgdf.sort_values(by=['megapixel', 'date', 'namepenalty', 'filesize', 'time'], ascending=[False,True,False,False,True]).iterrows():
        if (withInterventionUI):
            imgframe = create_image_frame(scrollable_frame, sortedimg, headers)
            imgframe.pack(side=tk.LEFT, padx=10, pady=10)
        if (indexsortedimg != 0): imagestodelete.append(sortedimg.id)
    
    if (withInterventionUI):
        # Create a frame for buttons below the scrollable content
        button_frame = tk.Frame(main_frame)
        button_frame.pack(side="bottom", fill="x", pady=10)
        
        # All buttons
        close_btn = tk.Button(button_frame, text="Skip", command=window.destroy,
                            bg="gray", fg="white", font=("Arial", 20))
        terminate_btn = tk.Button(button_frame, text="Terminate", command=exit,
                                bg="red", fg="white", font=("Arial", 20))
        delete_dups_btn = tk.Button(button_frame, text="Delete All except first one", command=lambda: delete_duplicates(imagestodelete),
                                bg="red", fg="white", font=("Arial", 10))
        
        # Pack buttons horizontally
        close_btn.pack(side=tk.LEFT, padx=5)
        terminate_btn.pack(side=tk.LEFT, padx=5)
        delete_dups_btn.pack(side=tk.LEFT, padx=5)
        window.mainloop()
    else:
        delete_duplicates(imagestodelete)
    



