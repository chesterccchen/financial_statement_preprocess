import os
from pdf2image import convert_from_path

pdf_folder=""
output_folder=""

for filename in os.listdir(pdf_folder):
    if filename.lower().endswith(".pdf"):
        pdf_path=os.path.join(pdf_folder,filename)
        base_name=os.path.splitext(filename)[0]

        images = convert_from_path(pdf_path, fmt='jpg')
        if len(images) ==1:
            output_path=os.path.join(output_folder,f"{base_name}.jpg")
            images[0].save(output_path,'JPEG')
        else:
            for i,img in enumerate(images,start=1):
                output_path=os.path.join(output_folder,f"{base_name}_{i}.jpg")
                img.save(output_path,"JPEG")
print("所有 PDF 轉換完成。")