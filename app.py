import streamlit as st
import qrcode
from PIL import Image
import io
import zipfile
import urllib.parse

# Page configuration
st.set_page_config(page_title="Bulk UPI QR Generator", page_icon="🔲", layout="wide")

st.title("🔲 Bulk UPI QR Code Generator")
st.markdown("Generate high-quality, 300 DPI QR codes for print. Just paste your list of UPI IDs below.")

# Input area for UPI IDs
st.markdown("### 1. Input UPI IDs")
default_input = """Paytmqr65ec57@ptys
paytmqr6nz7vx@ptys
32038020228860.loan@janabank
7877993040@okbizaxis"""

upi_list_text = st.text_area(
    "Paste your UPI IDs here (one per line):", 
    height=250, 
    value=default_input
)

# Configuration Options
st.markdown("### 2. Configuration")
col1, col2 = st.columns(2)
with col1:
    add_upi_prefix = st.checkbox(
        "Format as Scannable Payment Link", 
        value=True, 
        help="Adds 'upi://pay?pa=' so standard scanner apps recognize it as a payment."
    )
with col2:
    payee_name = st.text_input(
        "Default Payee Name (Optional):", 
        value="", 
        help="Adds a name parameter (&pn=Name) to the QR code."
    )

# Action Section
st.markdown("### 3. Generate & Download")
if st.button("🚀 Generate QR Codes", type="primary", use_container_width=True):
    if not upi_list_text.strip():
        st.error("Please enter at least one UPI ID.")
    else:
        # Clean up the input list (remove empty lines and spaces)
        raw_ids = [line.strip() for line in upi_list_text.split('\n') if line.strip()]
        
        # Prepare an in-memory ZIP file
        zip_buffer = io.BytesIO()
        generated_images = []
        
        # Create a progress bar
        progress_text = "Generating High-Res QR Codes..."
        progress_bar = st.progress(0, text=progress_text)
        
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for i, uid in enumerate(raw_ids):
                # 1. Construct the data string
                if add_upi_prefix:
                    qr_data = f"upi://pay?pa={uid}"
                    if payee_name:
                        safe_name = urllib.parse.quote(payee_name)
                        qr_data += f"&pn={safe_name}"
                else:
                    qr_data = uid
                    
                # 2. Generate the QR Code
                # Using ERROR_CORRECT_H (High) for maximum reliability if printed and slightly damaged
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_H,
                    box_size=25,  # Large box size ensures high resolution
                    border=4,
                )
                qr.add_data(qr_data)
                qr.make(fit=True)
                
                # Create PilImage object
                img = qr.make_image(fill_color="black", back_color="white").get_image()
                
                # 3. Save to an in-memory buffer with 300 DPI
                img_buffer = io.BytesIO()
                # Applying 300 DPI explicitly for A4 print quality
                img.save(img_buffer, format="PNG", dpi=(300, 300))
                img_bytes = img_buffer.getvalue()
                
                # Add to display preview list (limiting preview to 40 to save browser memory)
                if i < 40:
                    generated_images.append((uid, img_bytes))
                    
                # 4. Add the image to the ZIP file
                # Create a safe filename by replacing special characters with underscores
                safe_filename = "".join([c if c.isalnum() else "_" for c in uid])
                zip_file.writestr(f"{i+1:03d}_{safe_filename}.png", img_bytes)
                
                # Update progress
                progress_bar.progress((i + 1) / len(raw_ids), text=f"Processing {i+1} of {len(raw_ids)}...")
                
        progress_bar.empty()
        st.success(f"✅ Successfully generated {len(raw_ids)} high-resolution QR codes!")
        
        # Center the download button
        _, dl_col, _ = st.columns([1, 2, 1])
        with dl_col:
            st.download_button(
                label="📦 Download All as ZIP (300 DPI PNGs)",
                data=zip_buffer.getvalue(),
                file_name="Bulk_UPI_QRCodes.zip",
                mime="application/zip",
                use_container_width=True
            )
        
        # Display Preview Grid
        st.markdown("---")
        st.markdown(f"### Preview (Showing up to {min(40, len(raw_ids))})")
        
        cols = st.columns(4)
        for idx, (uid, img_bytes) in enumerate(generated_images):
            with cols[idx % 4]:
                st.image(img_bytes, caption=uid, use_container_width=True)
