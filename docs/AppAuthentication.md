## Add Authentication in Azure App Service configuration
1. Click on `Authentication` from left menu.

  ![Authentication](Images/AppAuthentication.png)

2. Click on `+ Add Provider` to see a list of identity providers.

  ![Authentication Identity](Images/AppAuthenticationIdentity.png)

3. Click on `+ Add Provider` to see a list of identity providers.

  ![Add Provider](Images/AppAuthIdentityProvider.png)

4. Select the first option `Microsoft Entra Id` from the drop-down list.
 
 ![Add Provider](Images/AppAuthIdentityProviderAdd.png)

5. Accept the default values and click on `Add` button to go back to the previous page with the identify provider added.

 ![Add Provider](Images/AppAuthIdentityProviderAdded.png)

 ### Creating a new App Registration
1. Click on `Home` and select `Microsoft Entra ID`.

![Microsoft Entra ID](/ResearchAssistant/Deployment/images/aiStudio/MicrosoftEntraID.png)

2. Click on `App registrations`.

![App registrations](/ResearchAssistant/Deployment/images/aiStudio/Appregistrations.png)

3. Click on `+ New registration`.

![New Registrations](/ResearchAssistant/Deployment/images/aiStudio/NewRegistration.png)

4. Provide the `Name`, select supported account types as `Accounts in this organizational directory only(Contoso only - Single tenant)`, select platform as `Web`, enter/select the `URL` and register.

![Add Details](/ResearchAssistant/Deployment/images/aiStudio/AddDetails.png)

5. After application is created sucessfully, then click on `Add a Redirect URL`.

![Redirect URL](/ResearchAssistant/Deployment/images/aiStudio/AddRedirectURL.png)

6. Click on `+ Add a platform`.

![+ Add platform](/ResearchAssistant/Deployment/images/aiStudio/AddPlatform.png)

7. Click on `Web`.

![Web](/ResearchAssistant/Deployment/images/aiStudio/Web.png)

8. Enter the `web app URL` (Provide the app service name in place of XXXX) and Save. Then go back to [Step 4](https://github.com/microsoft/Build-your-own-AI-Assistant-Solution-Accelerator/blob/PSL-Authenticate-Doc/ResearchAssistant/Deployment/AIStudioDeployment.md#step-4-add-authentication-in-azure-app-service-configuration) and follow from _Point 4_ choose `Pick an existing app registration in this directory` from the Add an Identity Provider page and provide the newly registered App Name.

![Add Details](/ResearchAssistant/Deployment/images/aiStudio/WebAppURL.png)
